// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://ai-systems-2026.halla.ai',
  integrations: [
    starlight({
      title: 'AI 시스템 2026',
      description: '제주한라대학교 인공지능학과 4학년 — 에이전틱 워크플로우와 하네스 엔지니어링',
      defaultLocale: 'root',
      locales: {
        root: {
          label: '한국어',
          lang: 'ko',
        },
      },
      logo: {
        src: './src/assets/logo.svg',
      },
      editLink: {
        baseUrl: 'https://github.com/halla-ai/ai-systems-2026/edit/main/',
      },
      lastUpdated: true,
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/halla-ai/ai-systems-2026' },
      ],
      customCss: ['./src/styles/custom.css'],
      sidebar: [
        {
          label: '홈',
          items: [
            { label: '강의 소개', link: '/' },
            { label: '강의계획서', link: '/syllabus' },
          ],
        },
        {
          label: 'Phase 1: 에이전틱 시스템 기초',
          collapsed: false,
          items: [
            { label: '1주차: AI 시스템 패러다임 전환', link: '/weeks/week-01' },
            { label: '2주차: HOTL 거버넌스와 Governance-as-Code', link: '/weeks/week-02' },
            { label: '3주차: MCP 아키텍처와 에이전틱 도구 생태계', link: '/weeks/week-03' },
          ],
        },
        {
          label: 'Phase 2: 하네스 엔지니어링',
          collapsed: false,
          items: [
            { label: '4주차: 루프 패러다임 — 반복이 복잡성을 이긴다', link: '/weeks/week-04' },
            { label: '5주차: 컨텍스트 관리와 Context Rot 방지', link: '/weeks/week-05' },
            { label: '6주차: 인스트럭션 튜닝', link: '/weeks/week-06' },
          ],
        },
        {
          label: 'Phase 3: 멀티에이전트 SDLC',
          collapsed: true,
          items: [
            { label: '7주차: 멀티에이전트 SDLC 설계', link: '/weeks/week-07' },
            { label: '8주차: 플래닝 에이전트', link: '/weeks/week-08' },
            { label: '9주차: QA 에이전트', link: '/weeks/week-09' },
          ],
        },
        {
          label: 'Phase 4: 오픈소스 모델 & MLOps',
          collapsed: true,
          items: [
            { label: '10주차: 오픈소스 코딩 LLM과 로컬 배포', link: '/weeks/week-10' },
            { label: '11주차: vLLM 고처리량 추론 최적화', link: '/weeks/week-11' },
            { label: '12주차: 텔레메트리와 LLM-as-Judge', link: '/weeks/week-12' },
          ],
        },
        {
          label: 'Phase 5: 캡스톤 Ralphthon',
          collapsed: true,
          items: [
            { label: '13주차: 캡스톤 프로젝트 설계', link: '/weeks/week-13' },
            { label: '14주차: Ralphthon 실행', link: '/weeks/week-14' },
            { label: '15주차: 시스템 통합과 최종 테스트', link: '/weeks/week-15' },
            { label: '16주차: 최종 발표와 수업 마무리', link: '/weeks/week-16' },
          ],
        },
        {
          label: '실습과제',
          collapsed: true,
          items: [
            { label: '실습 개요', link: '/labs' },
            { label: 'Lab 01: 개발 환경 설정', link: '/labs/lab-01' },
            { label: 'Lab 02: 첫 번째 AI 코딩 에이전트', link: '/labs/lab-02' },
            { label: 'Lab 03: MCP 서버 구현', link: '/labs/lab-03' },
            { label: 'Lab 04: Ralph 루프 구현', link: '/labs/lab-04' },
            { label: 'Lab 05: 컨텍스트 관리 실습', link: '/labs/lab-05' },
            { label: 'Lab 06: 인스트럭션 튜닝', link: '/labs/lab-06' },
            { label: 'Lab 07: 멀티에이전트 파이프라인', link: '/labs/lab-07' },
            { label: 'Lab 08: 플래닝 에이전트 구현', link: '/labs/lab-08' },
            { label: 'Lab 09: QA 에이전트 구현', link: '/labs/lab-09' },
            { label: 'Lab 10: vLLM 배포 실습', link: '/labs/lab-10' },
            { label: 'Lab 11: 텔레메트리 & 모니터링', link: '/labs/lab-11' },
            { label: 'Lab 12: LLM-as-Judge 구현', link: '/labs/lab-12' },
          ],
        },
        {
          label: '캡스톤 프로젝트',
          collapsed: true,
          items: [
            { label: '캡스톤 개요', link: '/capstone' },
            { label: '팀 구성', link: '/capstone/teams' },
            { label: '평가 기준', link: '/capstone/rubric' },
            { label: '제출 현황', link: '/capstone/submissions' },
          ],
        },
        {
          label: '참고자료',
          collapsed: true,
          items: [
            { label: '참고자료 홈', link: '/reference' },
            { label: '개발 도구', link: '/reference/tools' },
            { label: 'AI 코딩 도구 선택', link: '/reference/tool-selection' },
            { label: '논문 & 자료', link: '/reference/papers' },
            { label: '용어집', link: '/reference/glossary' },
            { label: '인프라 가이드', link: '/reference/infrastructure' },
          ],
        },
        {
          label: '기여 가이드',
          collapsed: true,
          items: [
            { label: '기여 방법', link: '/contribute' },
            { label: 'PR 가이드', link: '/contribute/pr-guide' },
            { label: '콘텐츠 스타일', link: '/contribute/content-style' },
          ],
        },
      ],
    }),
  ],
});
