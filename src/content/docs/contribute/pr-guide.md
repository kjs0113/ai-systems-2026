---
title: PR 가이드
description: Pull Request 생성부터 머지까지 — 단계별 가이드
---

## PR 체크리스트

PR을 보내기 전 다음을 확인하세요:

- [ ] `pnpm run build`가 성공적으로 완료됨
- [ ] 마크다운 문법 오류 없음
- [ ] 한국어 맞춤법 검토 완료
- [ ] 이미지/링크 경로 정상 동작 확인
- [ ] 과제 제출 시: `assignments/[lab/week]-XX/[학번]/` 경로 확인

## 커밋 메시지 규칙

```
<type>: <설명>

# 예시
feat: 1주차 강의노트에 HOTL 다이어그램 추가
fix: 3주차 MIG 코드 예제 오류 수정
docs: Lab 04 제출 요구사항 명확화
chore: 의존성 업데이트
```

**타입**:
- `feat`: 새로운 콘텐츠 추가
- `fix`: 오류 수정
- `docs`: 문서 개선
- `style`: 포맷팅 변경 (내용 변경 없음)
- `chore`: 기타 관리 작업

## 과제 제출 PR

```
# PR 제목 형식
[제출] Lab 04 - 20230001 홍길동

# PR 내용 예시
## 제출 내용
- harness.sh 구현 (ralph 루프 + backpressure)
- PROMPT.md 작성 (3개 태스크)
- pytest 기반 테스트 스위트

## 실행 결과
- 2번 실패 후 성공하는 루프 로그 첨부
- 가비지 컬렉션 동작 확인
```

## 리뷰 프로세스

1. PR 생성 → GitHub Actions 자동 빌드 검증
2. 빌드 성공 → 교수/동료 리뷰
3. 리뷰 통과 → 머지 → 자동 배포

## 리뷰 응답 방법

리뷰어가 변경을 요청하면:

```bash
# 수정 후
git add .
git commit -m "fix: 리뷰 반영 - XXX 수정"
git push origin [브랜치명]
# PR이 자동으로 업데이트됨
```

## 흔한 실수

| 실수 | 해결 |
|------|------|
| 빌드 실패 | `pnpm run build` 로컬 실행 후 오류 확인 |
| 브랜치가 main보다 뒤처짐 | `git pull upstream main` 후 rebase |
| 과제 경로 오류 | `assignments/lab-XX/[학번]/` 형식 재확인 |
