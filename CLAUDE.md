---
description: 
alwaysApply: true
---

# VANALY - Sustainable AI Health Coach (Vana + Analysis)

## 1. 프로젝트 맥락 & 철학
- **핵심 가치:** 일관성(Consistency) 유지, 실시간 개입(Intervention), 제로 저지먼트(Zero-Judgment).
- **작동 원리:** '꿀꺽(Gulp)'하기 전 찰나의 순간에 개입하여 '참' 배고픔을 진단하고 루틴을 유지함.

## 2. 기술 스택 & 도구 (Core Tooling)
- **AI Model:** Claude 3.7 Sonnet (Cursor 내 4.6 선택 사용)
- **Stack:** Python (FastAPI), PWA (Vanilla JS/Tailwind CSS), SQLite.

## 3. 개발 규칙 (Strict Rules)
- **Coding:** Python 타입 힌트 필수, Tailwind CSS 전용 (Inline 스타일 금지).
- **Tone:** `humanizer` 스킬을 반영하여, 기계적인 조언이 아닌 공감 기반의 코칭 텍스트 생성.
- **Workflow:** 변경 사항 적용 전 반드시 설명하고 승인 후 진행.

## 4. 실행 명령어 (Commands)
- **Skills:** `sh skills.sh install` (스킬 설치/업데이트)
- **Dev Server:** `uvicorn backend.main:app --reload`

## [Core Protocol: The Interview First]
- **의무 사항:** 복잡한 기능 구현이나 대규모 리팩토링 요청 시, Claude는 즉시 코드를 작성하지 않는다.
- **작동 방식:** `AskUser` 도구나 질문 리스트를 통해 다음 사항을 인터뷰한다.
  1. 모호한 요구사항 확인
  2. 발생 가능한 엣지 케이스 (데이터 누락, 네트워크 오류 등)
  3. 기존 코드베이스와의 충돌 가능성
- **중단 지점:** 사용자가 "인터뷰 종료, 구현 시작"이라고 명시하기 전까지는 추측하여 코딩하지 않는다.
