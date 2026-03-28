import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.database import db
from backend.services.coach_ai import (
    get_coach_reply,
    get_opening_message,
    get_session_summary,
)

router = APIRouter(prefix="/coach", tags=["Coach"])


# ── Pydantic 스키마 ───────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    user_id: int
    situation: str | None = None   # "binge" | "stress" | "lonely" | None


class MessageSend(BaseModel):
    content: str


class SessionResponse(BaseModel):
    session_id: int
    opening_message: str
    is_crisis: bool = False


class MessageResponse(BaseModel):
    reply: str
    is_crisis: bool = False


class CloseResponse(BaseModel):
    summary: str


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _get_today_meals(conn, user_id: int) -> list[dict]:
    """
    오늘 식사 기록을 반환.
    AI가 "아침 탄수화물 75g → 혈당 저하로 인한 배고픔" 같은 추론을 할 수 있도록
    반드시 meal_context에 포함해야 함.
    """
    rows = conn.execute(
        """
        SELECT food_items, calories, carbs_g, protein_g, fat_g, eaten_at
        FROM meals
        WHERE user_id = ? AND date(eaten_at) = date('now', 'localtime')
        ORDER BY eaten_at
        """,
        (user_id,),
    ).fetchall()

    result = []
    for row in rows:
        d = dict(row)
        d["food_items"] = json.loads(d.get("food_items") or "[]")
        result.append(d)
    return result


def _load_session(conn, session_id: int, user_id: int) -> dict:
    row = conn.execute(
        "SELECT * FROM coach_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없어요.")
    return dict(row)


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.post(
    "/session",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="코칭 세션 시작",
    description=(
        "situation 파라미터로 이모지 상황(binge/stress/lonely)을 전달하면 "
        "사용자 타이핑 없이 AI가 즉각 공감 오프너를 반환합니다. "
        "오늘의 식단 기록을 자동으로 AI 컨텍스트에 주입합니다."
    ),
)
async def create_session(body: SessionCreate) -> SessionResponse:
    with db() as conn:
        if not conn.execute("SELECT id FROM users WHERE id = ?", (body.user_id,)).fetchone():
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없어요.")
        meal_context = _get_today_meals(conn, body.user_id)

    opening, is_crisis = await get_opening_message(body.situation, meal_context)

    now = datetime.now().isoformat()
    init_messages = [{"role": "assistant", "content": opening, "timestamp": now}]

    with db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO coach_sessions (user_id, situation, messages, meal_context)
            VALUES (?, ?, ?, ?)
            """,
            (
                body.user_id,
                body.situation,
                json.dumps(init_messages, ensure_ascii=False),
                json.dumps(meal_context, ensure_ascii=False),
            ),
        )
        session_id = cursor.lastrowid

    return SessionResponse(
        session_id=session_id,
        opening_message=opening,
        is_crisis=is_crisis,
    )


@router.post(
    "/session/{session_id}/message",
    response_model=MessageResponse,
    summary="메시지 전송 → AI 코치 응답",
)
async def send_message(
    session_id: int,
    user_id: int,
    body: MessageSend,
) -> MessageResponse:
    with db() as conn:
        session = _load_session(conn, session_id, user_id)

    messages     = json.loads(session["messages"])
    meal_context = json.loads(session["meal_context"] or "[]")
    situation    = session.get("situation")

    messages.append({
        "role": "user",
        "content": body.content,
        "timestamp": datetime.now().isoformat(),
    })

    reply, is_crisis = await get_coach_reply(messages, meal_context, situation)

    messages.append({
        "role": "assistant",
        "content": reply,
        "timestamp": datetime.now().isoformat(),
    })

    with db() as conn:
        conn.execute(
            """
            UPDATE coach_sessions
            SET messages = ?, is_crisis = MAX(is_crisis, ?)
            WHERE id = ?
            """,
            (json.dumps(messages, ensure_ascii=False), int(is_crisis), session_id),
        )

    return MessageResponse(reply=reply, is_crisis=is_crisis)


@router.post(
    "/session/{session_id}/close",
    response_model=CloseResponse,
    summary="세션 종료 — 요약 + 다음 단계 반환",
)
async def close_session(session_id: int, user_id: int) -> CloseResponse:
    with db() as conn:
        session = _load_session(conn, session_id, user_id)

    messages     = json.loads(session["messages"])
    meal_context = json.loads(session["meal_context"] or "[]")
    situation    = session.get("situation")

    summary = await get_session_summary(messages, meal_context, situation)

    with db() as conn:
        conn.execute(
            """
            UPDATE coach_sessions
            SET summary = ?, closed_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (summary, session_id),
        )

    return CloseResponse(summary=summary)
