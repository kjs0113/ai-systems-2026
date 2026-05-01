// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// 빌드 시점에 현재 주차/Phase 자동 계산 — 해당 Phase 사이드바가 펼쳐짐
const SEMESTER_START = new Date('2026-03-03'); // 1주차 시작일
const now = new Date();
const weekNum = Math.max(1, Math.min(16,
  Math.floor((now - SEMESTER_START) / (7 * 24 * 60 * 60 * 1000)) + 1
));
const activePhase = weekNum <= 3 ? 1 : weekNum <= 6 ? 2 : weekNum <= 9 ? 3 : weekNum <= 12 ? 4 : 5;

export default defineConfig({
  site: 'https://ai-systems-2026.halla.ai',
  integrations: [
    starlight({
      head: [
        {
          // 주차 페이지 진입 시 해당 Phase ± 1 사이드바 메뉴 동적 펼침
          tag: 'script',
          content: `
            document.addEventListener('DOMContentLoaded',function(){
              var m=location.pathname.match(/\\/(?:en\\/)?weeks\\/week-(\\d+)/);
              if(!m)return;
              var w=parseInt(m[1],10);
              var p=w<=3?1:w<=6?2:w<=9?3:w<=12?4:5;
              var details=document.querySelectorAll('.sidebar-content details');
              details.forEach(function(d){
                var lbl=d.querySelector('.group-label .large');
                if(!lbl)return;
                var t=lbl.textContent;
                for(var i=1;i<=5;i++){
                  if(t.indexOf('Phase '+i)!==-1){
                    if(Math.abs(i-p)<=1)d.setAttribute('open','');
                    else d.removeAttribute('open');
                    break;
                  }
                }
              });
            });
          `,
        },
      ],
      title: {
        ko: 'AI 시스템 2026',
        en: 'AI Systems 2026',
      },
      description: '제주한라대학교 인공지능학과 4학년 — 에이전틱 워크플로우와 하네스 엔지니어링',
      defaultLocale: 'root',
      locales: {
        root: {
          label: '한국어',
          lang: 'ko',
        },
        en: {
          label: 'English',
          lang: 'en',
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
      components: {
        ThemeSelect: './src/components/ThemeSelect.astro',
        LanguageSelect: './src/components/LanguageSelect.astro',
      },
      customCss: ['./src/styles/custom.css'],
      sidebar: [
        {
          label: '홈',
          translations: { en: 'Home' },
          items: [
            { label: '강의 소개', translations: { en: 'Course Introduction' }, link: '/' },
            { label: '강의계획서', translations: { en: 'Syllabus' }, link: '/syllabus' },
          ],
        },
        {
          label: 'Phase 1: 에이전틱 시스템 기초',
          translations: { en: 'Phase 1: Agentic System Foundations' },
          collapsed: Math.abs(1 - activePhase) > 1,
          items: [
            { label: '1주차: AI 시스템 패러다임 전환', translations: { en: 'Week 1: AI Systems Paradigm Shift' }, link: '/weeks/week-01' },
            { label: '2주차: HOTL 거버넌스와 Governance-as-Code', translations: { en: 'Week 2: HOTL Governance & Governance-as-Code' }, link: '/weeks/week-02' },
            { label: '3주차: MCP 아키텍처와 에이전틱 도구 생태계', translations: { en: 'Week 3: MCP Architecture & Agentic Tool Ecosystem' }, link: '/weeks/week-03' },
          ],
        },
        {
          label: 'Phase 2: 하네스 엔지니어링',
          translations: { en: 'Phase 2: Harness Engineering' },
          collapsed: Math.abs(2 - activePhase) > 1,
          items: [
            { label: '4주차: 루프 패러다임 — 반복이 복잡성을 이긴다', translations: { en: 'Week 4: Loop Paradigm — Iteration Beats Complexity' }, link: '/weeks/week-04' },
            { label: '5주차: 컨텍스트 관리와 Context Rot 방지', translations: { en: 'Week 5: Context Management & Preventing Context Rot' }, link: '/weeks/week-05' },
            { label: '6주차: 인스트럭션 튜닝', translations: { en: 'Week 6: Instruction Tuning' }, link: '/weeks/week-06' },
          ],
        },
        {
          label: 'Phase 3: 멀티에이전트 SDLC',
          translations: { en: 'Phase 3: Multi-Agent SDLC' },
          collapsed: Math.abs(3 - activePhase) > 1,
          items: [
            { label: '7주차: 멀티에이전트 SDLC 설계', translations: { en: 'Week 7: Multi-Agent SDLC Design' }, link: '/weeks/week-07' },
            { label: '8주차: 플래닝 에이전트', translations: { en: 'Week 8: Planning Agent' }, link: '/weeks/week-08' },
            { label: '9주차: QA 에이전트', translations: { en: 'Week 9: QA Agent' }, link: '/weeks/week-09' },
          ],
        },
        {
          label: 'Phase 4: 오픈소스 모델 & MLOps',
          translations: { en: 'Phase 4: Open-Source Models & MLOps' },
          collapsed: Math.abs(4 - activePhase) > 1,
          items: [
            { label: '10주차: 오픈소스 코딩 LLM과 로컬 배포', translations: { en: 'Week 10: Open-Source Coding LLMs & Local Deployment' }, link: '/weeks/week-10' },
            { label: '11주차: vLLM 고처리량 추론 최적화', translations: { en: 'Week 11: vLLM High-Throughput Inference Optimization' }, link: '/weeks/week-11' },
            { label: '12주차: 텔레메트리와 LLM-as-Judge', translations: { en: 'Week 12: Telemetry & LLM-as-Judge' }, link: '/weeks/week-12' },
          ],
        },
        {
          label: 'Phase 5: 캡스톤 Ralphthon',
          translations: { en: 'Phase 5: Capstone Ralphthon' },
          collapsed: Math.abs(5 - activePhase) > 1,
          items: [
            { label: '13주차: 캡스톤 프로젝트 설계', translations: { en: 'Week 13: Capstone Project Design' }, link: '/weeks/week-13' },
            { label: '14주차: Ralphthon 실행', translations: { en: 'Week 14: Ralphthon Execution' }, link: '/weeks/week-14' },
            { label: '15주차: 시스템 통합과 최종 테스트', translations: { en: 'Week 15: System Integration & Final Testing' }, link: '/weeks/week-15' },
            { label: '16주차: 최종 발표와 수업 마무리', translations: { en: 'Week 16: Final Presentations & Wrap-up' }, link: '/weeks/week-16' },
          ],
        },
        {
          label: '실습과제',
          translations: { en: 'Labs' },
          collapsed: true,
          items: [
            { label: '실습 개요', translations: { en: 'Labs Overview' }, link: '/labs' },
            { label: 'Lab 01: 개발 환경 설정', translations: { en: 'Lab 01: Development Environment Setup' }, link: '/labs/lab-01' },
            { label: 'Lab 02: 첫 번째 AI 코딩 에이전트', translations: { en: 'Lab 02: First AI Coding Agent' }, link: '/labs/lab-02' },
            { label: 'Lab 03: MCP 서버 구현', translations: { en: 'Lab 03: MCP Server Implementation' }, link: '/labs/lab-03' },
            { label: 'Lab 04: Ralph 루프 구현', translations: { en: 'Lab 04: Ralph Loop Implementation' }, link: '/labs/lab-04' },
            { label: 'Lab 05: 컨텍스트 관리 실습', translations: { en: 'Lab 05: Context Management Practice' }, link: '/labs/lab-05' },
            { label: 'Lab 06: 인스트럭션 튜닝', translations: { en: 'Lab 06: Instruction Tuning' }, link: '/labs/lab-06' },
            { label: 'Lab 07: 멀티에이전트 파이프라인', translations: { en: 'Lab 07: Multi-Agent Pipeline' }, link: '/labs/lab-07' },
            { label: 'Lab 08: 플래닝 에이전트 구현', translations: { en: 'Lab 08: Planning Agent Implementation' }, link: '/labs/lab-08' },
            { label: 'Lab 09: QA 에이전트 구현', translations: { en: 'Lab 09: QA Agent Implementation' }, link: '/labs/lab-09' },
            { label: 'Lab 10: vLLM 배포 실습', translations: { en: 'Lab 10: vLLM Deployment Practice' }, link: '/labs/lab-10' },
            { label: 'Lab 11: 텔레메트리 & 모니터링', translations: { en: 'Lab 11: Telemetry & Monitoring' }, link: '/labs/lab-11' },
            { label: 'Lab 12: LLM-as-Judge 구현', translations: { en: 'Lab 12: LLM-as-Judge Implementation' }, link: '/labs/lab-12' },
          ],
        },
        {
          label: '캡스톤 프로젝트',
          translations: { en: 'Capstone Project' },
          collapsed: true,
          items: [
            { label: '캡스톤 개요', translations: { en: 'Capstone Overview' }, link: '/capstone' },
            { label: '팀 구성', translations: { en: 'Team Formation' }, link: '/capstone/teams' },
            { label: '평가 기준', translations: { en: 'Rubric' }, link: '/capstone/rubric' },
            { label: '제출 현황', translations: { en: 'Submissions' }, link: '/capstone/submissions' },
          ],
        },
        {
          label: '참고자료',
          translations: { en: 'Reference' },
          collapsed: true,
          items: [
            { label: '참고자료 홈', translations: { en: 'Reference Home' }, link: '/reference' },
            { label: '개발 도구', translations: { en: 'Development Tools' }, link: '/reference/tools' },
            { label: 'AI 코딩 도구 선택', translations: { en: 'AI Coding Tool Selection' }, link: '/reference/tool-selection' },
            { label: '논문 & 자료', translations: { en: 'Papers & Resources' }, link: '/reference/papers' },
            { label: '용어집', translations: { en: 'Glossary' }, link: '/reference/glossary' },
            { label: '인프라 가이드', translations: { en: 'Infrastructure Guide' }, link: '/reference/infrastructure' },
            { label: 'Claude Code 내부 구조', translations: { en: 'Claude Code Internals' }, link: '/reference/claude-code-internals' },
          ],
        },
        {
          label: '기여 가이드',
          translations: { en: 'Contributing' },
          collapsed: true,
          items: [
            { label: '기여 방법', translations: { en: 'How to Contribute' }, link: '/contribute' },
            { label: 'PR 가이드', translations: { en: 'PR Guide' }, link: '/contribute/pr-guide' },
            { label: '콘텐츠 스타일', translations: { en: 'Content Style' }, link: '/contribute/content-style' },
          ],
        },
      ],
    }),
  ],
});
