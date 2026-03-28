// ── DOM refs ──────────────────────────────────────────────────────────────────
const modal              = document.getElementById("coach-modal");
const backdrop           = document.getElementById("coach-backdrop");
const coachSheet         = document.getElementById("coach-sheet");
const closeBtn           = document.getElementById("coach-close-btn");
const situationPicker    = document.getElementById("situation-picker");
const chatMessages       = document.getElementById("chat-messages");
const chatInputArea      = document.getElementById("chat-input-area");
const chatInput          = document.getElementById("chat-input");
const chatSend           = document.getElementById("chat-send");
const typingIndicator    = document.getElementById("typing-indicator");
const crisisBanner       = document.getElementById("crisis-banner");
const sessionSummaryEl   = document.getElementById("session-summary");
const summaryText        = document.getElementById("summary-text");
const sosBtn             = document.getElementById("sos-btn");
// 브리딩 오버레이
const breathingOverlay   = document.getElementById("breathing-overlay");
const breathingCountEl   = document.getElementById("breathing-count");
const ringOuter          = document.getElementById("ring-outer");
const ringMid            = document.getElementById("ring-mid");
const ringInner          = document.getElementById("ring-inner");

// ── 상태 ─────────────────────────────────────────────────────────────────────
let sessionId   = null;
let isSending   = false;
let cachedUserId = null; // getOrCreateUserId() 성공 후 동기 접근용

// 사진 업로드 전에 SOS를 눌러도 user_id를 자동 생성
async function getOrCreateUserId() {
  const stored = localStorage.getItem("vanaly_user_id");
  if (stored) return parseInt(stored, 10);

  const res = await fetch("/users", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ name: "코치님" }),
  });
  if (!res.ok) throw new Error("사용자 생성 실패");
  const user = await res.json();
  localStorage.setItem("vanaly_user_id", String(user.id));
  cachedUserId = user.id;
  return user.id;
}

// ── 브리딩 오버레이 ───────────────────────────────────────────────────────────

/**
 * 3초 브리딩 세션 후 callback 실행.
 * 뇌과학적 마찰(friction): 충동 직후 즉각 반응하지 않고 3초 호흡으로 편도체 안정.
 * 브리딩 중 클릭 이벤트는 차단되며(pointer-events-none on overlay),
 * CSS 애니메이션 클래스를 매번 초기화해 재실행을 보장함.
 */
function startBreathing(callback) {
  // 동심원 애니메이션 클래스를 제거 → 리플로우 → 재추가 (재시작 보장)
  const rings = [
    [ringInner, "animate-breathe"],
    [ringMid,   "animate-breathe-d1"],
    [ringOuter, "animate-breathe-d2"],
  ];
  rings.forEach(([el, cls]) => {
    el.classList.remove(cls);
    void el.offsetWidth; // 강제 리플로우로 애니메이션 재시작
    el.classList.add(cls);
  });

  breathingOverlay.hidden = false;
  let count = 3;
  breathingCountEl.textContent = String(count);

  const timer = setInterval(() => {
    count -= 1;
    if (count > 0) {
      breathingCountEl.textContent = String(count);
    } else {
      clearInterval(timer);
      breathingOverlay.hidden = true;
      callback();
    }
  }, 1000);
}

// ── 모달 열기 / 닫기 ──────────────────────────────────────────────────────────

function openModal() {
  // 브리딩 3초 → 완료 후 모달 슬라이드업
  startBreathing(() => {
    resetModal();
    modal.hidden = false;

    // 바텀 시트 슬라이드업 애니메이션 재시작
    coachSheet.classList.remove("animate-slide-up");
    void coachSheet.offsetWidth;
    coachSheet.classList.add("animate-slide-up");

    closeBtn.focus();
  });
}

function closeModal() {
  // 요약은 백그라운드로 — X 버튼은 즉시 반응
  if (sessionId) fetchSummary();
  modal.hidden = true;
  sessionId    = null;
}

function resetModal() {
  sessionId = null;
  isSending = false;
  situationPicker.hidden  = false;
  chatMessages.hidden     = true;
  chatInputArea.hidden    = true;
  typingIndicator.hidden  = true;
  crisisBanner.hidden     = true;
  sessionSummaryEl.hidden = true;
  chatMessages.innerHTML  = "";
  chatInput.value         = "";
}

// ── 세션 시작 (이모지 선택 또는 skip) ────────────────────────────────────────

async function startSession(situation = null) {
  let userId;
  try {
    userId = await getOrCreateUserId();
    cachedUserId = userId;
  } catch {
    addBubble("assistant", "잠깐 연결이 안 됐어요. 서버가 켜져 있는지 확인해줘요. 🌿");
    chatMessages.hidden = false;
    situationPicker.hidden = true;
    return;
  }

  situationPicker.hidden = true;
  chatMessages.hidden    = false;
  showTyping();

  try {
    const res = await fetch("/coach/session", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ user_id: userId, situation }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    sessionId = data.session_id;
    hideTyping();
    addBubble("assistant", data.opening_message);
    if (data.is_crisis) showCrisisBanner();

    chatInputArea.hidden = false;
    chatInput.focus();

  } catch (err) {
    hideTyping();
    addBubble("assistant", "잠깐 연결이 안 됐어요. 다시 시도해줘요. 🌿");
    console.error("[VANALY Coach]", err);
  }
}

// ── 메시지 전송 ───────────────────────────────────────────────────────────────

async function sendMessage() {
  const content = chatInput.value.trim();
  if (!content || isSending || !sessionId) return;

  isSending = true;
  chatSend.disabled = true;
  chatInput.value   = "";
  autoResize();

  addBubble("user", content);
  showTyping();
  scrollToBottom();

  try {
    const userId = cachedUserId ?? parseInt(localStorage.getItem("vanaly_user_id") || "0", 10);
    const res = await fetch(
      `/coach/session/${sessionId}/message?user_id=${userId}`,
      {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ content }),
      }
    );

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    hideTyping();
    addBubble("assistant", data.reply);
    if (data.is_crisis) showCrisisBanner();

  } catch (err) {
    hideTyping();
    addBubble("assistant", "잠깐 문제가 생겼어요. 다시 말해줘도 괜찮아요. 🌿");
    console.error("[VANALY Coach]", err);
  } finally {
    isSending = false;
    chatSend.disabled = false;
    scrollToBottom();
  }
}

// ── 세션 종료 요약 ────────────────────────────────────────────────────────────

async function fetchSummary() {
  try {
    const userId = cachedUserId ?? parseInt(localStorage.getItem("vanaly_user_id") || "0", 10);
    const res = await fetch(
      `/coach/session/${sessionId}/close?user_id=${userId}`,
      { method: "POST" }
    );
    if (!res.ok) return;
    const data = await res.json();

    summaryText.textContent = data.summary;
    sessionSummaryEl.hidden = false;
    chatInputArea.hidden    = true;
    scrollToBottom();
  } catch (err) {
    console.error("[VANALY Coach close]", err);
  }
}

// ── UI 헬퍼 ───────────────────────────────────────────────────────────────────

function addBubble(role, text) {
  const isAssistant = role === "assistant";
  const wrapper = document.createElement("div");
  wrapper.className = `flex ${isAssistant ? "justify-start" : "justify-end"}`;

  const bubble = document.createElement("div");
  bubble.className = isAssistant
    ? "bg-gray-100 text-gray-800 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm leading-relaxed max-w-[80%]"
    : "bg-brand-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed max-w-[80%]";
  bubble.textContent = text;

  wrapper.appendChild(bubble);
  chatMessages.appendChild(wrapper);
  scrollToBottom();
}

function showTyping() {
  typingIndicator.hidden = false;
  scrollToBottom();
}

function hideTyping() {
  typingIndicator.hidden = true;
}

function showCrisisBanner() {
  crisisBanner.hidden = false;
}

function scrollToBottom() {
  const area = document.getElementById("chat-area");
  requestAnimationFrame(() => {
    area.scrollTop = area.scrollHeight;
  });
}

// textarea 높이 자동 조정
function autoResize() {
  chatInput.style.height = "auto";
  chatInput.style.height = Math.min(chatInput.scrollHeight, 96) + "px";
}

// ── 이벤트 바인딩 ─────────────────────────────────────────────────────────────

// 플로팅 SOS 버튼
sosBtn?.addEventListener("click", openModal);

// ── 모달 닫기 ─────────────────────────────────────────────────────────────────
// 시트 클릭이 백드롭으로 버블링되지 않도록 차단 (방어적 코딩)
coachSheet?.addEventListener("click", (e) => e.stopPropagation());

// X 버튼: 반드시 stopPropagation 후 닫기
closeBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  closeModal();
});

// 백드롭 클릭 (시트 외부)
backdrop?.addEventListener("click", closeModal);

// 이모지 상황 버튼
document.querySelectorAll(".situation-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const situation = btn.dataset.situation;
    startSession(situation);
  });
});

// 바로 시작
document.getElementById("skip-situation")?.addEventListener("click", () => {
  startSession(null);
});

// 전송
chatSend.addEventListener("click", sendMessage);
chatInput.addEventListener("keydown", (e) => {
  // e.isComposing: 한글 IME 조합 중일 때는 Enter를 무시해 마지막 글자 잔류 방지
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    sendMessage();
  }
});
chatInput.addEventListener("input", autoResize);

// ESC 키로 모달 닫기
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !modal.hidden) closeModal();
});
