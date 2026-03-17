# AI 시스템 2026

제주한라대학교 인공지능학과 4학년 강의 사이트 — **에이전틱 워크플로우와 하네스 엔지니어링**

**사이트**: [ai-systems-2026.halla.ai](https://ai-systems-2026.halla.ai)
**저장소**: [github.com/halla-ai/ai-systems-2026](https://github.com/halla-ai/ai-systems-2026)

---

## 강의 구성

| Phase | 주차 | 주제 |
|-------|------|------|
| 1 | 1–3주 | 에이전틱 시스템 기초 — HOTL, MIG, MCP |
| 2 | 4–6주 | 하네스 엔지니어링 — Ralph 루프, 컨텍스트 관리, 인스트럭션 튜닝 |
| 3 | 7–9주 | 멀티에이전트 SDLC — 플래닝/QA 에이전트 |
| 4 | 10–12주 | 오픈소스 모델 & MLOps — DeepSeek-Coder-V2, vLLM, LLM-as-Judge |
| 5 | 13–16주 | 캡스톤 Ralphthon — 설계 → 실행 → 발표 |

16주차 강의노트 · Lab 12개 · 캡스톤 프로젝트 포함 (총 44페이지)

---

## 기술 스택

- **Astro 6** + **Starlight 0.38** — 정적 문서 사이트
- **MDX** 콘텐츠 (Aside, Steps, Badge, Card 등 Starlight 컴포넌트)
- **Space Grotesk** + **Pretendard Variable** 폰트
- **GitHub Actions** → GitHub Pages 자동 배포

---

## 로컬 개발

```bash
make install   # 의존성 설치 (pnpm install --frozen-lockfile)
make dev       # 개발 서버 localhost:4321
make build     # 정적 빌드 → dist/
make preview   # 빌드 결과 미리보기
make status    # 콘텐츠 파일 현황
```

새 콘텐츠 스캐폴딩:

```bash
make new-week N=07   # src/content/docs/weeks/week-07.mdx 생성
make new-lab N=05    # src/content/docs/labs/lab-05.mdx 생성
```

---

## 콘텐츠 구조

```
src/content/docs/
├── index.mdx          # 홈 (splash)
├── syllabus.md        # 강의계획서
├── weeks/             # week-01.mdx ~ week-16.mdx
├── labs/              # lab-01.mdx ~ lab-12.mdx
├── capstone/          # 캡스톤 프로젝트 (팀, 루브릭, 제출)
├── reference/         # 도구, 논문, 용어집, 인프라
└── contribute/        # 기여 가이드
```

---

## 과제 제출

학생들은 GitHub PR로 과제를 제출한다.

```
assignments/lab-XX/[학번]/
assignments/week-XX/[학번]/
```

자세한 방법 → [기여 가이드](https://ai-systems-2026.halla.ai/contribute)

---

## 배포

`main` 브랜치 push 시 GitHub Actions가 자동으로 빌드·배포한다.
배포 설정: `.github/workflows/deploy.yml`
