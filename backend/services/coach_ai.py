import json
import os
from datetime import datetime

from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY 환경 변수가 없어요.")
        _client = AsyncOpenAI(api_key=api_key)
    return _client


# ── 상황별 즉각 공감 오프너 ────────────────────────────────────────────────────
# 이모지를 눌렀을 때 사용자가 타이핑 없이도 AI가 먼저 공감 대화를 시작

_OPENERS_KO: dict[str, str] = {
    "binge": (
        "아, 갑자기 많이 먹고 싶은 충동이 밀려오셨군요. "
        "몸이 무언가를 강하게 원하고 있는 것 같아요. "
        "지금 이 느낌, 어디서 오는 건지 같이 살펴봐도 괜찮을까요? 🌿"
    ),
    "stress": (
        "아, 스트레스로 많이 힘드시군요. 정말 고생하셨어요. "
        "제가 여기 옆에 있을게요. "
        "오늘 어떤 일이 있었는지 편하게 이야기해주시겠어요?"
    ),
    "lonely": (
        "지금 이 순간 저를 찾아주셔서 정말 고마워요. "
        "혼자가 아니에요. "
        "어떤 마음인지 천천히, 편하게 들려주셔도 괜찮아요. 🤍"
    ),
}

_OPENERS_EN: dict[str, str] = {
    "binge": (
        "Hey, sounds like a strong urge to eat just hit you. "
        "Your body is really craving something right now. "
        "Want to gently explore together where this feeling is coming from? 🌿"
    ),
    "stress": (
        "Ah, it sounds like stress has been really weighing on you — you've been holding a lot. "
        "I'm right here with you. "
        "Would you feel comfortable sharing what's been going on today?"
    ),
    "lonely": (
        "I'm really glad you reached out in this moment. "
        "You're not alone. "
        "Take your time — there's no rush, just share whatever feels right. 🤍"
    ),
}

# ── 위기 키워드 (응답에 [[CRISIS]] 플래그 삽입 트리거) ────────────────────────
_CRISIS_KEYWORDS = [
    "죽고싶", "죽고 싶", "자살", "자해", "없어지고 싶",
    "살기 싫", "살기싫", "사라지고 싶", "힘들어 죽겠", "못 살겠",
]


# ── 상황별 코칭 미션 정의 ────────────────────────────────────────────────────

_MISSION: dict[str | None, str] = {
    "binge": """\
[현재 미션: 폭식 충동 개입 — 가장 중요]
사용자가 폭식 충동을 느끼고 있습니다. 당신의 역할은 충동을 '판단 없이 막아주는 것'입니다.

절대 해서는 안 되는 것:
- 크로와상·과자·라면·치킨 등 고칼로리 음식을 권유하거나 "한 입 드세요" 식의 표현
- "배고프면 먹어도 괜찮아요"처럼 충동을 그대로 긍정하는 말

반드시 해야 하는 것:
1. 감정 인정: 충동이 느껴지는 것 자체를 따뜻하게 인정 (음식이 아닌 감정에 공감)
2. 충동 재해석: 혈당 저하·스트레스·습관 루프 중 오늘 식단과 연결되는 원인 1가지 설명
3. 리디렉션 제안(1가지만): 물 한 잔 / 10분만 기다리기 / 5분 산책 / 저당 간식 중 하나를 자연스럽게 제안

예시 응답 방향:
"아, 갑자기 크로와상이 너무 먹고 싶어졌군요. 오늘 아침에 탄수화물을 꽤 드셨으니 지금 이 충동은 혈당이 살짝 내려가며 보내는 신호일 수 있어요. 일단 물 한 잔 마시고 10분만 같이 버텨봐요. 그래도 생각나면 그때 다시 이야기해요."
""",
    "stress": """\
[현재 미션: 스트레스 감정 코칭]
사용자가 스트레스를 받고 있습니다. 감정을 충분히 들어주되, 스트레스성 폭식으로 이어지지 않도록 돌봐주세요.
스트레스 해소를 위한 음식 섭취를 권장하지 마세요. 대신 감정 자체를 풀 수 있는 방향으로 대화를 유도하세요.
""",
    "lonely": """\
[현재 미션: 외로움·감정 지지 코칭]
사용자가 혼자라는 느낌을 받고 있습니다. 따뜻한 존재감을 전달하고, 감정적 허기를 음식으로 채우려는 충동이 생기지 않도록 함께해주세요.
""",
    None: """\
[현재 미션: 일반 감정·영양 코칭]
사용자의 이야기를 듣고 감정과 오늘 식단 데이터를 연결해 공감 기반의 코칭을 제공하세요.
""",
}


# ── 시스템 프롬프트 — 오늘 식단 데이터 + 상황 미션 주입 ──────────────────────

_LANG_INSTRUCTION: dict[str, str] = {
    "ko": "반드시 한국어로만 응답하세요. 영어를 절대 사용하지 마세요.",
    "en": "Always respond in English only. Do not use any Korean.",
}


def build_system_prompt(
    meal_context: list[dict],
    situation: str | None = None,
    lang: str = "ko",
) -> str:
    """
    오늘의 식단 기록, 상황별 코칭 미션, 언어 지시를 AI 컨텍스트에 주입한다.
    - binge: 폭식 충동 개입 — 고칼로리 권유 절대 금지, 리디렉션 필수
    - stress / lonely: 감정 지지 중심
    - None: 일반 식단 코칭
    - lang: "ko" | "en"
    """
    if meal_context:
        lines = []
        for meal in meal_context:
            foods = ", ".join(meal.get("food_items") or [])
            cal   = meal.get("calories", 0)
            carbs = meal.get("carbs_g", 0.0)
            prot  = meal.get("protein_g", 0.0)
            fat   = meal.get("fat_g", 0.0)
            ts    = (meal.get("eaten_at") or "")[:16]
            lines.append(
                f"- {ts} | {foods} "
                f"({cal}kcal, 탄수화물 {carbs:.0f}g, 단백질 {prot:.0f}g, 지방 {fat:.0f}g)"
            )
        meal_summary = "\n".join(lines)
        total_carbs = sum(m.get("carbs_g", 0) for m in meal_context)
        total_cal   = sum(m.get("calories", 0) for m in meal_context)
    else:
        meal_summary  = "오늘 기록된 식사 없음"
        total_carbs   = 0
        total_cal     = 0

    # situation이 _MISSION에 없으면 None(일반) 미션 사용
    mission = _MISSION.get(situation, _MISSION[None])
    lang_instruction = _LANG_INSTRUCTION.get(lang, _LANG_INSTRUCTION["ko"])

    return f"""\
당신은 VANALY의 따뜻한 감정·영양 코치입니다.

[언어 규칙 — 최우선]
{lang_instruction}


{mission}

━━━ 오늘의 식단 기록 (반드시 대화에 활용) ━━━
{meal_summary}
합계: 총 {total_cal}kcal / 탄수화물 {total_carbs:.0f}g
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[혈당·컨디션 분석 지침]
- 아침에 탄수화물이 많았다면(>50g) → "오늘 아침에 탄수화물을 꽤 드셨으니 지금 배고픔이 혈당이 떨어진 신호일 수 있어요"라고 자연스럽게 언급
- 식단 데이터를 기계적으로 나열하지 말고 대화 맥락에 자연스럽게 녹여낼 것

[코칭 스타일 — 3-Beat]
1. 공감(Empathy): 판단 없이 감정을 먼저 인정 (1문장)
2. 인사이트(Insight): 식단 데이터와 연결되는 신체·감정 신호 설명 (1문장)
3. 초대(Invitation): 현재 미션에 맞는 다음 작은 단계 제안 (1문장)

[위기 감지]
자해·자살 관련 표현이 있으면 반드시 응답 마지막에 [[CRISIS]] 를 붙이세요.

[절대 금지 — 판단 언어]
"실패했네요", "그건 나빠요", "틀렸어요", "넌 왜 그래요" 같은 비판·수치심 유발 표현

[응답 규칙]
- 항상 한국어
- 2~4문장 이내로 간결하게
- 친한 친구처럼 — 의사·트레이너 말투 금지
"""


# ── API 호출 ──────────────────────────────────────────────────────────────────

async def get_opening_message(
    situation: str | None,
    meal_context: list[dict],
    lang: str = "ko",
) -> tuple[str, bool]:
    """이모지 선택 시 즉각 반환(preset) 또는 AI 생성 오프너."""
    openers = _OPENERS_EN if lang == "en" else _OPENERS_KO
    if situation and situation in openers:
        return openers[situation], False

    # 상황 미선택 → AI가 오늘 식단을 참고해 맞춤 오프닝 생성
    client = _get_client()
    opening_instruction = (
        "Start with a warm one-sentence greeting in English, referencing today's meal data. "
        "Do not include crisis hotline numbers."
        if lang == "en" else
        "[세션 시작] 오늘 식단을 참고해 따뜻한 한 문장 오프닝을 만들어주세요. "
        "1393 등 위기 번호는 포함하지 마세요."
    )
    fallback = (
        "I'm really glad you're here. Feel free to share whatever's on your mind. 🌿"
        if lang == "en" else
        "지금 이 순간 찾아주셔서 고마워요. 어떤 마음인지 편하게 이야기해줘요. 🌿"
    )
    res = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=120,
        messages=[
            {"role": "system", "content": build_system_prompt(meal_context, lang=lang)},
            {"role": "user", "content": opening_instruction},
        ],
    )
    msg = res.choices[0].message.content or fallback
    return msg, False


async def get_coach_reply(
    messages: list[dict],
    meal_context: list[dict],
    situation: str | None = None,
    lang: str = "ko",
) -> tuple[str, bool]:
    """사용자 메시지에 대한 코치 응답 생성. (reply_text, is_crisis) 반환."""
    client  = _get_client()
    system  = build_system_prompt(meal_context, situation, lang)

    chat = [{"role": "system", "content": system}]
    for m in messages:
        chat.append({"role": m["role"], "content": m["content"]})

    res = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=200,
        messages=chat,
    )

    raw       = res.choices[0].message.content or ""
    is_crisis = "[[CRISIS]]" in raw
    clean     = raw.replace("[[CRISIS]]", "").strip()
    return clean, is_crisis


async def get_session_summary(
    messages: list[dict],
    meal_context: list[dict],
    situation: str | None = None,
    lang: str = "ko",
) -> str:
    """세션 종료 시 따뜻한 요약 + 다음 단계 제안."""
    client = _get_client()
    system = build_system_prompt(meal_context, situation, lang)

    chat = [{"role": "system", "content": system}]
    for m in messages:
        chat.append({"role": m["role"], "content": m["content"]})
    chat.append({
        "role": "user",
        "content": (
            "[대화 마무리] 1~2문장으로 따뜻하게 정리하고 "
            "다음 단계(식사, 휴식, 산책 등)를 하나만 부드럽게 제안해주세요."
        ),
    })

    res = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=120,
        messages=chat,
    )
    return res.choices[0].message.content or "오늘 함께해서 고마워요. 잘 지내요 🌿"
