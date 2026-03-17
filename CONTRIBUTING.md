# 기여 가이드

AI 시스템 2026 강의 사이트에 기여해 주셔서 감사합니다!
이 가이드는 학생 여러분이 강의 자료에 기여하는 방법을 설명합니다.

## 빠른 시작

```bash
# 1. 저장소 Fork (GitHub에서 우측 상단 Fork 버튼 클릭)

# 2. 로컬 클론
git clone https://github.com/[YOUR_USERNAME]/ai-systems-2026.git
cd ai-systems-2026

# 3. 의존성 설치
pnpm install

# 4. 개발 서버 실행
pnpm run dev
# → http://localhost:4321 에서 미리보기

# 5. 수정 후 빌드 확인
pnpm run build
```

## 과제 제출 방법

과제는 GitHub PR을 통해 제출합니다:

```
assignments/
├── week-01/
│   └── [학번]/          # 예: 20230001/
│       └── README.md
├── lab-01/
│   └── [학번]/
│       ├── README.md
│       └── (코드 파일들)
```

1. Fork 후 `assignments/[lab/week]-XX/[학번]/` 폴더에 파일 추가
2. PR 제목: `[제출] Lab 01 - 20230001 홍길동`
3. PR 설명에 구현 내용 간략히 작성

## PR 규칙

- `main` 브랜치로 PR 보내기
- PR 전 `pnpm run build` 성공 확인 필수
- 커밋 메시지는 한국어 가능: `feat: 1주차 강의노트 보충 설명 추가`

## 오류 신고

강의 자료에서 오류를 발견했나요?
[GitHub Issue](https://github.com/halla-ai/ai-systems-2026/issues/new?template=content-error.md)를 통해 신고해 주세요.

## 궁금한 점

[기여 가이드 페이지](/contribute)에서 더 자세한 내용을 확인하세요.
