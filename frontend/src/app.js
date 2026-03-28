// ── 상태 관리 ─────────────────────────────────────────────────────────────────

const views = {
  upload:  document.getElementById("upload-view"),
  loading: document.getElementById("loading-view"),
  result:  document.getElementById("result-view"),
};

function showView(name) {
  Object.values(views).forEach((v) => { v.hidden = true; });
  views[name].hidden = false;
}

// ── 사용자 생성 / 복구 (localStorage 기반) ────────────────────────────────────

async function getOrCreateUserId() {
  const stored = localStorage.getItem("vanaly_user_id");
  if (stored) return parseInt(stored, 10);

  const res = await fetch("/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "코치님" }),
  });
  if (!res.ok) throw new Error("사용자 생성 실패");

  const user = await res.json();
  localStorage.setItem("vanaly_user_id", String(user.id));
  return user.id;
}

// ── 에러 표시 ─────────────────────────────────────────────────────────────────

function showError(message) {
  const el = document.getElementById("error-msg");
  el.textContent = message;
  el.hidden = false;
  showView("upload");
}

// ── 결과 렌더링 ───────────────────────────────────────────────────────────────

function renderResult(data, file) {
  // 이미지 미리보기
  const img = document.getElementById("result-image");
  img.src = URL.createObjectURL(file);

  // 음식명 + 신뢰도
  document.getElementById("food-items").textContent =
    data.food_items.length ? data.food_items.join(", ") : "음식 정보 없음";
  document.getElementById("confidence").textContent =
    `${Math.round((data.confidence ?? 0) * 100)}%`;

  // 코치 메시지
  document.getElementById("feedback-text").textContent =
    data.feedback_text || "분석이 완료됐어요!";
  document.getElementById("next-meal-text").textContent =
    data.next_meal_suggestion || "";

  // 칼로리
  document.getElementById("calories").textContent = data.calories ?? 0;

  // 매크로
  document.getElementById("carbs").textContent   = `${(data.carbs_g   ?? 0).toFixed(1)}g`;
  document.getElementById("protein").textContent = `${(data.protein_g ?? 0).toFixed(1)}g`;
  document.getElementById("fat").textContent     = `${(data.fat_g     ?? 0).toFixed(1)}g`;
  document.getElementById("fiber").textContent   = `${(data.fiber_g   ?? 0).toFixed(1)}g`;

  // 나트륨
  document.getElementById("sodium").textContent =
    `${Math.round(data.sodium_mg ?? 0).toLocaleString("ko-KR")}mg`;

  // 혈당 영향
  const impactLabel = { low: "💚 낮음", medium: "🟡 보통", high: "🔴 높음" };
  const impactEl = document.getElementById("blood-sugar");
  impactEl.textContent = impactLabel[data.blood_sugar_impact] ?? data.blood_sugar_impact;
  impactEl.className =
    data.blood_sugar_impact === "high"   ? "font-medium text-red-500" :
    data.blood_sugar_impact === "medium" ? "font-medium text-yellow-500" :
                                           "font-medium text-green-500";

  // 에너지 피크
  document.getElementById("energy-peak").textContent =
    `약 ${data.energy_peak_minutes ?? 45}분 후`;
}

// ── 이미지 분석 메인 흐름 ─────────────────────────────────────────────────────

async function analyzeFile(file) {
  // 에러 메시지 초기화
  document.getElementById("error-msg").hidden = true;
  showView("loading");

  try {
    const userId = await getOrCreateUserId();

    const formData = new FormData();
    formData.append("user_id", String(userId));
    formData.append("file", file);

    const res = await fetch("/meals/analyze", {
      method: "POST",
      body: formData,
    });

    const body = await res.json();

    if (!res.ok) {
      // 422: 음식 아닌 사진 or 흐린 이미지 → 친절한 안내
      const detail = body?.detail ?? "분석 중 문제가 생겼어요. 다시 시도해줘요.";
      showError(detail);
      return;
    }

    renderResult(body, file);
    showView("result");

  } catch (err) {
    console.error("[VANALY] analyze error:", err);
    showError("서버와 연결할 수 없어요. 잠시 후 다시 시도해줘요.");
  }
}

// ── 파일 입력 핸들러 설정 ─────────────────────────────────────────────────────

function setupInputs() {
  const galleryInput = document.getElementById("gallery-input");
  const cameraInput  = document.getElementById("camera-input");
  const uploadArea   = document.getElementById("upload-area");

  // 갤러리 — 레이블 클릭이 이미 input 트리거함
  galleryInput.addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (file) analyzeFile(file);
    e.target.value = "";
  });

  // 카메라 버튼
  document.getElementById("camera-btn").addEventListener("click", () =>
    cameraInput.click()
  );
  cameraInput.addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (file) analyzeFile(file);
    e.target.value = "";
  });

  // 드래그 & 드롭
  uploadArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadArea.classList.add("dragover");
  });
  uploadArea.addEventListener("dragleave", () =>
    uploadArea.classList.remove("dragover")
  );
  uploadArea.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadArea.classList.remove("dragover");
    const file = e.dataTransfer?.files?.[0];
    if (file?.type.startsWith("image/")) analyzeFile(file);
  });

  // 다시 분석하기
  document.getElementById("retry-btn").addEventListener("click", () => {
    document.getElementById("error-msg").hidden = true;
    showView("upload");
  });
}

// ── 헬스체크 배지 ─────────────────────────────────────────────────────────────

async function checkHealth() {
  const dot   = document.getElementById("health-dot");
  const label = document.getElementById("health-label");
  try {
    const res = await fetch("/health");
    if (res.ok) {
      dot.className   = "w-2 h-2 rounded-full bg-green-400";
      label.textContent = "연결됨";
    } else {
      throw new Error();
    }
  } catch {
    dot.className   = "w-2 h-2 rounded-full bg-red-400";
    label.textContent = "오프라인";
  }
}

// ── 초기화 ────────────────────────────────────────────────────────────────────
setupInputs();
checkHealth();
showView("upload");
