// ── 언어 감지 ─────────────────────────────────────────────────────────────────
// localStorage 우선 → 브라우저 설정 → 기본 'ko'
const stored = localStorage.getItem("vanaly_lang");
export const lang = stored ?? (navigator.language?.startsWith("ko") ? "ko" : "en");
localStorage.setItem("vanaly_lang", lang);

// ── 번역 테이블 ───────────────────────────────────────────────────────────────
const TRANSLATIONS = {
  en: {
    // Header
    healthChecking:    "Checking",
    healthConnected:   "Connected",
    healthOffline:     "Offline",

    // Welcome card
    welcomeTitle:      "Welcome! Let's build your rhythm together. ✨",
    welcomeSubtitle:   "Feeling hungry? Take a breath first.",

    // Slogan
    slogan:            "Empower Your Rhythm. Guided Every Step by Your Personal Coach.",

    // Upload zone
    uploadHint:        "Drop your meal photo here",
    uploadFormats:     "JPEG · PNG · WebP · Max 10MB",
    cameraBtnText:     "Take a photo",

    // Loading
    analyzing:         "VANALY is analyzing your meal... 🥗",

    // Result
    detectedFood:      "Detected foods",
    aiConfidence:      "AI confidence",
    coachCardTitle:    "Coach's Message",
    nextMealTitle:     "💡 Next meal suggestion",
    nutritionTitle:    "Nutrition",
    labelCarbs:        "Carbs",
    labelProtein:      "Protein",
    labelFat:          "Fat",
    labelFiber:        "Fiber",
    labelSodium:       "Sodium",
    labelBloodSugar:   "Blood sugar impact",
    labelEnergyPeak:   "Energy peak est.",
    retryBtn:          "🔄 Analyze another",
    bloodSugarLow:     "💚 Low",
    bloodSugarMedium:  "🟡 Medium",
    bloodSugarHigh:    "🔴 High",
    energyPeakFmt:     "~{n} min",

    // Floating SOS
    sosBtnText:        "Find Calm",

    // Breathing overlay
    breatheIn:         "Take a deep breath in",
    breatheOut:        "and slowly breathe out",

    // Coach modal
    modalTitle:        "Find Calm 🕊️",
    modalSubtitle:     "Your AI coach is here",
    situationQ:        "How are you feeling right now?",
    situationBinge:    "Binge Urge",
    situationStress:   "Stressed",
    situationLonely:   "Just Rough",
    skipBtn:           "Jump right in →",
    chatPlaceholder:   "Share what's on your mind...",
    sendBtn:           "Send",
    crisisTitle:       "💛 Need professional support?",
    crisisDesc:        "Crisis counseling · 24/7 · Free · Anonymous",
    summaryTitle:      "Today's session recap 🌿",
    closeModal:        "Close modal",

    // Errors (JS dynamic)
    errGeneric:        "Something went wrong. Please try again.",
    errOffline:        "Can't reach the server. Please try again later.",
    errUserCreate:     "Connection issue. Is the server running? 🌿",
    errConnectSession: "Connection issue. Please check the server. 🌿",
    errReply:          "Something went wrong. Feel free to try again. 🌿",
  },

  ko: {
    // Header
    healthChecking:    "확인 중",
    healthConnected:   "연결됨",
    healthOffline:     "오프라인",

    // Welcome card
    welcomeTitle:      "반가워요! 오늘의 리듬을 함께 만들어봐요. ✨",
    welcomeSubtitle:   "지금 배고프신가요? 먼저 한 숨 쉬어봐요.",

    // Slogan
    slogan:            "당신의 리듬을 깨우는 시간, 늘 곁에 있는 퍼스널 가이드.",

    // Upload zone
    uploadHint:        "식단 사진을 여기에 올려주세요",
    uploadFormats:     "JPEG · PNG · WebP · 최대 10MB",
    cameraBtnText:     "카메라로 촬영하기",

    // Loading
    analyzing:         "VANALY가 식단을 분석 중이에요... 🥗",

    // Result
    detectedFood:      "인식된 음식",
    aiConfidence:      "AI 신뢰도",
    coachCardTitle:    "코치의 따뜻한 한마디",
    nextMealTitle:     "💡 다음 식사 제안",
    nutritionTitle:    "영양 성분",
    labelCarbs:        "탄수화물",
    labelProtein:      "단백질",
    labelFat:          "지방",
    labelFiber:        "식이섬유",
    labelSodium:       "나트륨",
    labelBloodSugar:   "혈당 영향",
    labelEnergyPeak:   "에너지 피크 예상",
    retryBtn:          "🔄 다시 분석하기",
    bloodSugarLow:     "💚 낮음",
    bloodSugarMedium:  "🟡 보통",
    bloodSugarHigh:    "🔴 높음",
    energyPeakFmt:     "약 {n}분 후",

    // Floating SOS
    sosBtnText:        "평온 찾기",

    // Breathing overlay
    breatheIn:         "깊게 숨을 들이마시고",
    breatheOut:        "천천히 내쉬어보세요",

    // Coach modal
    modalTitle:        "평온 찾기 🕊️",
    modalSubtitle:     "AI 코치가 함께해요",
    situationQ:        "지금 어떤 마음인가요?",
    situationBinge:    "폭식 충동",
    situationStress:   "스트레스",
    situationLonely:   "그냥 힘들어",
    skipBtn:           "그냥 바로 시작할게요 →",
    chatPlaceholder:   "마음을 편하게 적어보세요...",
    sendBtn:           "전송",
    crisisTitle:       "💛 전문 도움이 필요하신가요?",
    crisisDesc:        "정신건강 위기상담 · 24시간 · 무료 · 익명 가능",
    summaryTitle:      "오늘의 대화 정리 🌿",
    closeModal:        "모달 닫기",

    // Errors (JS dynamic)
    errGeneric:        "분석 중 문제가 생겼어요. 다시 시도해줘요.",
    errOffline:        "서버와 연결할 수 없어요. 잠시 후 다시 시도해줘요.",
    errUserCreate:     "잠깐 연결이 안 됐어요. 서버가 켜져 있는지 확인해줘요. 🌿",
    errConnectSession: "잠깐 연결이 안 됐어요. 서버가 켜져 있는지 확인해줘요. 🌿",
    errReply:          "잠깐 문제가 생겼어요. 다시 말해줘도 괜찮아요. 🌿",
  },
};

// ── 번역 함수 ─────────────────────────────────────────────────────────────────

/**
 * 키로 번역 문자열 반환. {n} 같은 플레이스홀더는 params로 치환.
 * 예: t("energyPeakFmt", { n: 45 }) → "~45 min" or "약 45분 후"
 */
export function t(key, params = {}) {
  const str =
    TRANSLATIONS[lang]?.[key] ??
    TRANSLATIONS["en"][key] ??
    key;
  return str.replace(/\{(\w+)\}/g, (_, k) => (params[k] ?? `{${k}}`));
}

// ── DOM 일괄 적용 ─────────────────────────────────────────────────────────────

/**
 * [data-i18n="key"]          → el.textContent = t(key)
 * [data-i18n-placeholder]    → el.placeholder  = t(key)
 * [data-i18n-aria]           → el.ariaLabel    = t(key)
 */
export function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
    el.setAttribute("aria-label", t(el.dataset.i18nAria));
  });

  // <html lang> 속성 업데이트 (스크린 리더·SEO)
  document.documentElement.lang = lang;
}
