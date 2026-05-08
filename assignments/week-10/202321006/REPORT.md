# [Lab 10] vLLM 배포 실습 및 오픈소스 모델 분석

**학번:** 202321006  
**제출일:** 2026-05-08

## 1. vLLM 모델 배포 결과 (DGX 서버)
DGX 서버 환경에서 `vLLM`을 사용하여 `Qwen3-Coder-32B-Instruct` 모델을 성공적으로 배포하였습니다.

### 배포 로그 (Summary)
```text
INFO 05-05 10:00:25 api_server.py:214] Starting vLLM API server on http://localhost:8000
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```
*(상세 로그는 `logs/vllm_deploy.log` 참조)*

## 2. 코딩 성능 비교 (Qwen3-Coder vs Claude)
동일한 5개 코딩 태스크(알고리즘, 데이터 처리, 디버깅, 아키텍처, 테스트)를 수행한 결과, Qwen3-Coder-32B는 상용 모델인 Claude-3.5-Sonnet의 약 90% 수준의 구현 능력을 보여주었습니다.

- **강점:** 알고리즘 구현 및 문법 정확도
- **약점:** 복잡한 시스템 설계 시의 가이드라인 제시
*(상세 비교 데이터는 `artifacts/performance_comparison.md` 참조)*

## 3. 처리량(Throughput) 벤치마크 결과
`vLLM` 벤치마크 도구를 통한 측정 결과입니다.
- **처리량:** 2636.8 tokens/sec
- **평균 지연시간:** 242.71 ms
*(상세 결과는 `logs/throughput_results.log` 참조)*

## 4. 비용 분석 (API vs DGX)
연간 대량의 토큰(일 1,000만)을 사용하는 시나리오에서, DGX 서버를 활용한 로컬 배포는 상용 API 대비 **약 72% 이상의 비용 절감 효과**가 있는 것으로 분석되었습니다.

| 구분 | 연간 비용 (추정) | 비고 |
| :--- | :--- | :--- |
| **Claude API** | $24,090 | 사용량 비례 증가 |
| **DGX Local** | 약 675만원 | 인프라 기보유 전제 |

## 5. 결론 및 고찰
오픈소스 모델의 발전으로 인해 데이터 프라이버시가 중요하거나 사용량이 매우 많은 경우, DGX와 같은 고성능 로컬 인프라에서 vLLM을 통해 모델을 운영하는 것이 기술적/경제적으로 매우 타당한 선택임을 확인하였습니다. 특히 Qwen3-Coder-32B 모델은 실무에 즉시 투입 가능한 수준의 성능을 보여주었습니다.
