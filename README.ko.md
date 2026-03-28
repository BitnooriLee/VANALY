# VANALY — 지속 가능한 AI 건강 코치

> "꿀꺽"하기 전 찰나의 순간, 참 배고픔을 진단하고 일관성 있는 루틴을 유지합니다.

[English README →](README.md)

---

## 핵심 가치

| 가치 | 설명 |
|---|---|
| **일관성 (Consistency)** | 매일 쌓이는 식단·감정 데이터로 리듬을 만든다 |
| **실시간 개입 (Intervention)** | 충동이 올라오는 순간 3초 브리딩으로 편도체를 안정시킨다 |
| **제로 저지먼트 (Zero Judgment)** | 판단 없이, 친한 친구처럼 곁에 있는다 |

---

## 기술 스택

- **Backend**: Python 3.12 · FastAPI · SQLite
- **Frontend**: Vanilla JS · Tailwind CSS (CDN) · PWA
- **AI**: GPT-4o Vision (식단 분석) · GPT-4o-mini (감정 코칭)
- **i18n**: 브라우저 언어 자동 감지 (한국어 / 영어)

---

## 프로젝트 구조

```
VANALY/
├── backend/
│   ├── main.py              # FastAPI 앱 진입점, 라우터 등록
│   ├── database.py          # SQLite 연결, 스키마 초기화 및 마이그레이션
│   ├── routers/
│   │   ├── users.py         # 사용자 생성·조회·목표 관리
│   │   ├── meals.py         # 식단 사진 업로드·분석·이력
│   │   └── coach.py         # AI 코칭 세션 생성·대화·종료
│   └── services/
│       ├── vision.py        # GPT-4o Vision 이미지 분석
│       └── coach_ai.py      # 감정 코칭 AI (상황별 미션 프롬프트)
├── frontend/
│   ├── index.html           # PWA 메인 화면
│   ├── src/
│   │   ├── i18n.js          # 언어 감지 + t() 번역 함수 모듈
│   │   ├── app.js           # 식단 업로드·결과 렌더링
│   │   └── coach.js         # 브리딩 오버레이·코칭 모달
│   ├── manifest.json
│   └── service-worker.js    # 네트워크-퍼스트 캐싱 전략
├── requirements.txt
├── .env.example
└── CLAUDE.md                # AI 개발 규칙 및 프로젝트 철학
```

---

## 구현된 기능

### 1. 식단 분석 엔진
- 사진 업로드(갤러리 / 카메라 / 드래그&드롭) → GPT-4o Vision 분석
- 반환값: 음식명, 칼로리, 탄·단·지·섬유, 나트륨, 혈당 영향, 에너지 피크 예상
- 오늘 총 섭취 기록을 컨텍스트로 주입 → "아침 탄수화물 75g → 지금 배고픔이 혈당 저하 신호" 추론
- 음식이 아닌 사진·흐린 이미지는 친절한 안내 메시지로 처리

### 2. 평온 찾기 (AI 감정 코칭)
- **3초 브리딩 Friction**: 버튼 클릭 즉시 화면 전체 블러 오버레이 + 동심원 팽창 애니메이션 + 카운트다운. 충동이 올라오는 순간 편도체를 가라앉히는 뇌과학 기반 UX
- 브리딩 완료 후 바텀 시트 슬라이드업으로 코칭 모달 진입
- **상황별 즉각 공감 오프너**: 폭식충동 🍔 / 스트레스 😮‍💨 / 그냥 힘들어 🫂 선택 시 AI가 먼저 따뜻하게 말 걸기
- **상황별 코칭 미션**: `binge` 시 고칼로리 음식 권유 절대 금지 + 리디렉션(물, 10분 기다리기, 산책) 의무화
- 오늘의 식단 데이터를 실시간 주입 → 맥락 기반 코칭
- 위기 키워드 감지 시 1393 정신건강 위기상담 배너 자동 노출
- 세션 종료 시 따뜻한 요약 + 다음 단계 제안

### 3. 이중 언어 지원 (한국어 / 영어)
- 첫 로드 시 `navigator.language` 감지 → `localStorage`에 저장
- UI 텍스트, AI 코칭 응답, 식단 분석 피드백 모두 감지된 언어로 서비스

### 4. PWA
- 오프라인 캐싱 (서비스 워커, 네트워크-퍼스트 전략)
- 홈 화면 추가 지원 (manifest.json)
- 모바일 최적화 레이아웃

---

## 실행 방법

```bash
# 1. 환경 설정
cp .env.example .env
# .env에 OPENAI_API_KEY 입력

# 2. 가상환경 설치
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 서버 실행
uvicorn backend.main:app --reload
# → http://127.0.0.1:8000
```

---

## API 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| `GET` | `/health` | 서버 상태 확인 |
| `POST` | `/users` | 사용자 생성 |
| `GET` | `/users/{id}` | 사용자 조회 |
| `PUT` | `/users/{id}/goals` | 영양 목표 설정 |
| `POST` | `/meals/analyze` | 식단 사진 분석 |
| `GET` | `/meals/history` | 식단 이력 조회 |
| `POST` | `/coach/session` | 코칭 세션 시작 |
| `POST` | `/coach/session/{id}/message` | 메시지 전송 |
| `POST` | `/coach/session/{id}/close` | 세션 종료·요약 |

> 전체 API 문서: `http://127.0.0.1:8000/docs`

---

## 환경 변수

```
OPENAI_API_KEY=sk-...
```
