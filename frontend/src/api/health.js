// 프론트와 백엔드가 같은 오리진(localhost:8000)이므로 상대경로 사용
const API_BASE = "";

/**
 * @returns {Promise<{status: string, service: string, timestamp: string}>}
 */
export async function fetchHealth() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);

  try {
    const res = await fetch(`${API_BASE}/health`, { signal: controller.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(timeout);
  }
}
