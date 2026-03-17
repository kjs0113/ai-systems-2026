---
title: 기여 방법
description: 강의 사이트에 기여하는 방법 — Fork, 수정, PR 가이드
---

## 기여 가이드

이 사이트의 모든 내용은 GitHub에서 관리됩니다. 학생 여러분의 기여가 강의를 더 좋게 만들어요!

## 기여할 수 있는 것들

- **오류 수정**: 강의 내용의 오탈자, 코드 오류 수정
- **설명 보완**: 불명확한 개념에 추가 설명 기여
- **실습 팁**: 트러블슈팅 경험 공유
- **참고자료 추가**: 유용한 논문, 블로그 링크 추가
- **과제 제출**: `assignments/` 폴더에 본인 과제 PR

## 빠른 시작

```bash
# 1. GitHub에서 Fork (오른쪽 상단 Fork 버튼)

# 2. 로컬 클론
git clone https://github.com/[YOUR_USERNAME]/ai-systems-2026.git
cd ai-systems-2026

# 3. 의존성 설치
pnpm install

# 4. 개발 서버 실행
pnpm run dev
# → http://localhost:4321

# 5. 수정 후 빌드 확인 (PR 전 필수!)
pnpm run build
```

## PR 생성 과정

```bash
# 새 브랜치 생성
git checkout -b fix/week-03-typo

# 수정 후 커밋
git add .
git commit -m "fix: 3주차 MIG 설명 오탈자 수정"

# 푸시
git push origin fix/week-03-typo

# GitHub에서 PR 생성
```

## 더 읽기

- [PR 가이드](/contribute/pr-guide) — PR 체크리스트와 리뷰 프로세스
- [콘텐츠 스타일](/contribute/content-style) — 강의 자료 작성 규칙
