import json
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from backend.database import UPLOADS_DIR, db
from backend.models.schemas import MealAnalysisResponse, MealListResponse
from backend.services.vision import analyze_meal_image

router = APIRouter(prefix="/meals", tags=["Meals"])

_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
_MAX_SIZE_MB = 10


# ── 유틸 ─────────────────────────────────────────────────────────────────────

def _get_user_or_404(conn, user_id: int) -> dict:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없어요.")
    return dict(row)


def _get_goals(conn, user_id: int) -> dict:
    row = conn.execute(
        "SELECT * FROM user_goals WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    if row:
        return dict(row)
    return {
        "daily_calories": 2000,
        "carbs_pct": 50.0,
        "protein_pct": 25.0,
        "fat_pct": 25.0,
        "goal_type": "maintenance",
    }


def _get_today_summary(conn, user_id: int) -> tuple[int, list[str]]:
    """오늘 이미 먹은 칼로리 합계 + 음식명 목록 반환."""
    rows = conn.execute(
        """
        SELECT calories, food_items FROM meals
        WHERE user_id = ?
          AND date(eaten_at) = date('now', 'localtime')
        ORDER BY eaten_at
        """,
        (user_id,),
    ).fetchall()

    total_cal = 0
    foods: list[str] = []
    for row in rows:
        total_cal += row["calories"] or 0
        if row["food_items"]:
            foods.extend(json.loads(row["food_items"]))

    return total_cal, foods


def _row_to_response(row: dict) -> MealAnalysisResponse:
    return MealAnalysisResponse(
        id=row["id"],
        user_id=row["user_id"],
        food_items=json.loads(row["food_items"] or "[]"),
        calories=row["calories"] or 0,
        carbs_g=row["carbs_g"] or 0.0,
        protein_g=row["protein_g"] or 0.0,
        fat_g=row["fat_g"] or 0.0,
        fiber_g=row["fiber_g"] or 0.0,
        sodium_mg=row["sodium_mg"] or 0.0,
        glycemic_load=row["glycemic_load"] or 0.0,
        blood_sugar_impact=row["blood_sugar_impact"] or "medium",
        energy_peak_minutes=row["energy_peak_minutes"] or 45,
        confidence=row["confidence"] or 0.0,
        feedback_text=row["feedback_text"] or "",
        next_meal_suggestion=row["next_meal_suggestion"] or "",
        eaten_at=row["eaten_at"],
    )


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=MealAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="식단 사진 분석",
    description="사진을 업로드하면 GPT-4o Vision으로 영양소를 분석하고 humanizer 코칭 피드백을 반환합니다.",
)
async def analyze_meal(
    user_id: int = Form(..., description="사용자 ID"),
    file: UploadFile = File(..., description="식단 사진 (JPEG/PNG/WebP/HEIC)"),
    lang: str = Form("ko", description="응답 언어 (ko | en)"),
) -> MealAnalysisResponse:
    # ── 파일 유효성 검사 ──────────────────────────────────────────────────────
    if file.content_type not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"지원하지 않는 파일 형식이에요. ({', '.join(_ALLOWED_MIME)})",
        )

    raw_bytes = await file.read()
    if len(raw_bytes) > _MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기는 {_MAX_SIZE_MB}MB 이하여야 해요.",
        )

    # ── 사용자·목표·오늘 식사 내역 조회 ──────────────────────────────────────
    with db() as conn:
        _get_user_or_404(conn, user_id)
        goals = _get_goals(conn, user_id)
        calories_today, foods_today = _get_today_summary(conn, user_id)

    # ── Vision 분석 호출 ──────────────────────────────────────────────────────
    result = await analyze_meal_image(
        image_bytes=raw_bytes,
        user_goals=goals,
        calories_eaten_today=calories_today,
        previous_foods=foods_today,
        lang=lang,
    )

    # 음식 아닌 사진 / 흐린 이미지 에러 처리
    if "error" in result:
        messages = {
            "not_food": "음식 사진이 아닌 것 같아요. 드시려는 음식을 찍어서 올려줘요 🍱",
            "unclear": "사진이 너무 흐리거나 어두워서 분석하기 어려워요. 밝은 곳에서 다시 찍어봐요 📸",
        }
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=messages.get(result["error"], "분석 중 문제가 생겼어요. 잠시 후 다시 시도해줘요."),
        )

    # ── 이미지 저장 ───────────────────────────────────────────────────────────
    filename = f"{uuid.uuid4().hex}.jpg"
    image_path = str(UPLOADS_DIR / filename)
    Path(image_path).write_bytes(raw_bytes)

    # ── DB 저장 ───────────────────────────────────────────────────────────────
    with db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO meals (
                user_id, image_path, food_items, calories,
                carbs_g, protein_g, fat_g, fiber_g, sodium_mg,
                glycemic_load, blood_sugar_impact, energy_peak_minutes,
                confidence, feedback_text, next_meal_suggestion, raw_analysis
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                user_id,
                f"uploads/{filename}",
                json.dumps(result.get("food_items", []), ensure_ascii=False),
                result.get("total_calories", 0),
                result.get("carbs_g", 0.0),
                result.get("protein_g", 0.0),
                result.get("fat_g", 0.0),
                result.get("fiber_g", 0.0),
                result.get("sodium_mg", 0.0),
                result.get("glycemic_load", 0.0),
                result.get("blood_sugar_impact", "medium"),
                result.get("energy_peak_minutes", 45),
                result.get("confidence", 0.0),
                result.get("feedback_text", ""),
                result.get("next_meal_suggestion", ""),
                json.dumps(result, ensure_ascii=False),
            ),
        )
        meal_id = cursor.lastrowid

        row = conn.execute("SELECT * FROM meals WHERE id = ?", (meal_id,)).fetchone()

    return _row_to_response(dict(row))


@router.get(
    "/history",
    response_model=MealListResponse,
    summary="식사 기록 조회",
)
def get_meal_history(
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> MealListResponse:
    with db() as conn:
        _get_user_or_404(conn, user_id)

        rows = conn.execute(
            """
            SELECT * FROM meals
            WHERE user_id = ?
            ORDER BY eaten_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        ).fetchall()

        total = conn.execute(
            "SELECT COUNT(*) FROM meals WHERE user_id = ?", (user_id,)
        ).fetchone()[0]

    return MealListResponse(
        meals=[_row_to_response(dict(r)) for r in rows],
        total=total,
    )


@router.delete(
    "/{meal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="식사 기록 삭제",
)
def delete_meal(meal_id: int, user_id: int) -> None:
    with db() as conn:
        affected = conn.execute(
            "DELETE FROM meals WHERE id = ? AND user_id = ?",
            (meal_id, user_id),
        ).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="해당 식사 기록을 찾을 수 없어요.")
