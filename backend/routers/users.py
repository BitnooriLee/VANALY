from fastapi import APIRouter, HTTPException, status

from backend.database import db
from backend.models.schemas import GoalsResponse, GoalsUpdate, UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="사용자 생성",
    description="첫 방문 시 호출. user_id를 클라이언트 localStorage에 저장해 이후 요청에 사용하세요.",
)
def create_user(body: UserCreate) -> UserResponse:
    with db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name) VALUES (?)", (body.name,)
        )
        user_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO user_goals (user_id) VALUES (?)", (user_id,)
        )
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

    return UserResponse(**dict(row))


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="사용자 조회",
)
def get_user(user_id: int) -> UserResponse:
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없어요.")
    return UserResponse(**dict(row))


@router.put(
    "/{user_id}/goals",
    response_model=GoalsResponse,
    summary="목표 설정·수정",
)
def update_goals(user_id: int, body: GoalsUpdate) -> GoalsResponse:
    # 탄단지 비율 합계 검증
    total = body.carbs_pct + body.protein_pct + body.fat_pct
    if not (99.0 <= total <= 101.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"탄수화물·단백질·지방 비율 합계는 100이어야 해요. (현재: {total:.1f})",
        )

    with db() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없어요.")

        existing = conn.execute(
            "SELECT id FROM user_goals WHERE user_id = ?", (user_id,)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE user_goals
                SET daily_calories = ?, carbs_pct = ?, protein_pct = ?,
                    fat_pct = ?, goal_type = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE user_id = ?
                """,
                (
                    body.daily_calories, body.carbs_pct, body.protein_pct,
                    body.fat_pct, body.goal_type, user_id,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO user_goals
                    (user_id, daily_calories, carbs_pct, protein_pct, fat_pct, goal_type)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id, body.daily_calories, body.carbs_pct,
                    body.protein_pct, body.fat_pct, body.goal_type,
                ),
            )

        goals_row = conn.execute(
            "SELECT * FROM user_goals WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()

    return GoalsResponse(**dict(goals_row))


@router.get(
    "/{user_id}/goals",
    response_model=GoalsResponse,
    summary="목표 조회",
)
def get_goals(user_id: int) -> GoalsResponse:
    with db() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없어요.")

        goals_row = conn.execute(
            "SELECT * FROM user_goals WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()

    if not goals_row:
        raise HTTPException(status_code=404, detail="목표가 설정되지 않았어요.")
    return GoalsResponse(**dict(goals_row))
