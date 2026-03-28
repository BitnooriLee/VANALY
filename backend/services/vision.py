import base64
import io
import json
import os

from openai import AsyncOpenAI
from PIL import Image

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되지 않았어요.")
        _client = AsyncOpenAI(api_key=api_key)
    return _client


# ── 이미지 전처리 — 토큰 절감을 위해 768px 이하로 리사이즈 ─────────────────────

def preprocess_image(raw_bytes: bytes, max_px: int = 768) -> bytes:
    img = Image.open(io.BytesIO(raw_bytes))

    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    w, h = img.size
    if max(w, h) > max_px:
        ratio = max_px / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()


# ── GPT-4o Vision 프롬프트 ───────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are VANALY, an expert nutritionist AI specializing in Korean and Asian cuisine.

Analyze the food image provided. Return ONLY valid JSON — no markdown, no explanation.

──────────────────────────────────────────
CASE 1 — Image contains NO food:
{"error": "not_food"}

CASE 2 — Image is too blurry / dark / unrecognizable:
{"error": "unclear"}

CASE 3 — Food detected → return full analysis:
{
  "food_items": ["음식명1", "음식명2"],
  "total_calories": <integer>,
  "carbs_g": <float>,
  "protein_g": <float>,
  "fat_g": <float>,
  "fiber_g": <float>,
  "sodium_mg": <float>,
  "glycemic_load": <float 0–100>,
  "blood_sugar_impact": "<low|medium|high>",
  "energy_peak_minutes": <integer>,
  "confidence": <float 0–1>
}
──────────────────────────────────────────

Rules:
- Use Korean food database portions as baseline (밥 한 공기 = 210g, 국 = 200ml, etc.)
- glycemic_load: (GI × carbs_g) / 100
- blood_sugar_impact: low < 10, medium 10–19, high ≥ 20
- energy_peak_minutes: simple carbs ≈ 20–30 min, mixed ≈ 40–60 min, high-fiber ≈ 60–90 min
- confidence: lower if multiple items, sauces obscure food, or image is partially cropped
"""


def _build_user_prompt(
    daily_calories: int,
    goal_type: str,
    calories_eaten_today: int,
    previous_foods: list[str],
) -> str:
    remaining = daily_calories - calories_eaten_today
    prev = "없음" if not previous_foods else ", ".join(previous_foods[-6:])

    return (
        f"[사용자 컨텍스트]\n"
        f"- 오늘 목표 칼로리: {daily_calories} kcal\n"
        f"- 오늘 섭취한 칼로리: {calories_eaten_today} kcal (남은 여유: {remaining} kcal)\n"
        f"- 오늘 이전 식사: {prev}\n"
        f"- 목표 유형: {goal_type}\n\n"
        "위 사진의 음식을 분석해줘."
    )


_COACHING_SYSTEM_KO = """\
You are VANALY, a warm and non-judgmental Korean health coach.

You receive a JSON nutritional analysis and user context, then write a coaching message in KOREAN.

Follow the 3-Beat pattern strictly:
1. 공감(Empathy): Acknowledge the current meal without judgment (1 sentence)
2. 인사이트(Insight): One nutritional or blood-sugar insight relevant to the user's goals (1–2 sentences)
3. 초대(Invitation): A gentle, specific next-meal suggestion (1 sentence)

Return JSON only:
{
  "feedback_text": "<3-beat coaching message in Korean, 3–5 sentences total>",
  "next_meal_suggestion": "<specific food idea for the next meal in Korean, 1 sentence>"
}

Rules:
- RESPOND IN KOREAN ONLY
- NEVER use: 실패, 과식, 나쁜, 안 됩니다, 해야 합니다
- ALWAYS empathize first
- Keep total under 120 characters per field
- Sound like a caring friend, not a clinical report
"""

_COACHING_SYSTEM_EN = """\
You are VANALY, a warm and non-judgmental health coach.

You receive a JSON nutritional analysis and user context, then write a coaching message in ENGLISH.

Follow the 3-Beat pattern strictly:
1. Empathy: Acknowledge the current meal without judgment (1 sentence)
2. Insight: One nutritional or blood-sugar insight relevant to the user's goals (1–2 sentences)
3. Invitation: A gentle, specific next-meal suggestion (1 sentence)

Return JSON only:
{
  "feedback_text": "<3-beat coaching message in English, 3–5 sentences total>",
  "next_meal_suggestion": "<specific food idea for the next meal in English, 1 sentence>"
}

Rules:
- RESPOND IN ENGLISH ONLY
- NEVER use words like: failed, overate, bad, you must, you should not
- ALWAYS empathize first
- Keep total under 120 characters per field
- Sound like a caring friend, not a clinical report
"""


# ── 메인 서비스 함수 ──────────────────────────────────────────────────────────

async def analyze_meal_image(
    image_bytes: bytes,
    user_goals: dict,
    calories_eaten_today: int,
    previous_foods: list[str],
    lang: str = "ko",
) -> dict:
    """
    Returns either:
      {"error": "not_food" | "unclear"}
    or a full nutrition + coaching dict.
    """
    client = _get_client()
    processed = preprocess_image(image_bytes)
    b64 = base64.b64encode(processed).decode()

    user_prompt = _build_user_prompt(
        daily_calories=user_goals.get("daily_calories", 2000),
        goal_type=user_goals.get("goal_type", "maintenance"),
        calories_eaten_today=calories_eaten_today,
        previous_foods=previous_foods,
    )

    # ── Step 1: Vision 분석 ──────────────────────────────────────────────────
    vision_response = await client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        max_tokens=512,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "low",  # 토큰 절감
                        },
                    },
                ],
            },
        ],
    )

    nutrition = json.loads(vision_response.choices[0].message.content or "{}")

    # 에러 케이스 조기 반환
    if "error" in nutrition:
        return nutrition

    # ── Step 2: 코칭 피드백 생성 (텍스트 전용 — 저렴) ────────────────────────
    coaching_system = _COACHING_SYSTEM_EN if lang == "en" else _COACHING_SYSTEM_KO
    coaching_response = await client.chat.completions.create(
        model="gpt-4o-mini",  # 피드백은 저렴한 모델로 충분
        response_format={"type": "json_object"},
        max_tokens=256,
        messages=[
            {"role": "system", "content": coaching_system},
            {
                "role": "user",
                "content": (
                    f"Nutrition analysis: {json.dumps(nutrition, ensure_ascii=False)}\n"
                    f"User context: {user_prompt}"
                ),
            },
        ],
    )

    coaching = json.loads(coaching_response.choices[0].message.content or "{}")

    return {**nutrition, **coaching}
