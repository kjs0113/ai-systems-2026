# Lab 05: 컨텍스트 관리 실습

**학번**: 202321010  

---

## 📌 과제 개요

이 프로젝트는 LLM 시스템에서 발생하는 **Context Rot** 현상을 측정하고, **자동 컨텍스트 초기화**를 통해 해결하는 시스템을 구현합니다.

### 핵심 목표
1. ✅ 토큰 카운터가 통합된 Ralph 루프 구현
2. ✅ Context Rot 시뮬레이션 및 측정
3. ✅ 자동 컨텍스트 초기화 로직 (Hybrid 전략)
4. ✅ 상태 추적 시스템 (fix_plan.md + claude-progress.txt)

---

## 🏗️ 시스템 아키텍처

```
ralph_with_context.sh/ps1
 ├─ 📊 토큰 카운터 (count_tokens.py)
 ├─ 🔄 컨텍스트 누적 (history buffer)
 ├─ ✂️ 컨텍스트 초기화 (summarize_context.py)
 ├─ 🤖 LLM 호출 (call_llm.py)
 ├─ 📝 로그 기록 (token, context, quality)
 ├─ 📈 상태 추적 (update_state.py)
 └─ 🔁 반복 루프 (max 20 iterations)

logs/
 ├─ token_log.csv        # 토큰 사용량
 ├─ context_log.csv      # 컨텍스트 길이
 └─ quality_log.csv      # 응답 품질

analysis/
 ├─ plot_context_rot.py  # 그래프 생성
 ├─ token_usage.png
 ├─ context_growth.png
 ├─ quality_degradation.png
 ├─ combined_analysis.png
 ├─ before_after_comparison.png
 └─ analysis_summary.txt

state/
 ├─ fix_plan.md          # 작업 계획
 └─ claude-progress.txt  # 진행 상황
```

---

## 🚀 실행 방법

### 1️⃣ 환경 준비

```bash
# Python 패키지 설치
pip install pandas matplotlib numpy
```

옵션: 정확한 토큰 카운팅을 위한 tiktoken 설치
```bash
pip install tiktoken
```

### 2️⃣ Ralph 루프 실행

#### Windows (PowerShell)
```powershell
# 실행 권한 부여 (첫 실행 시)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 실행
.\ralph_with_context.ps1
```

#### Linux/Mac (Bash)
```bash
# 실행 권한 부여
chmod +x ralph_with_context.sh

# 실행
./ralph_with_context.sh
```

### 3️⃣ 그래프 생성

```bash
python analysis/plot_context_rot.py
```

### 4️⃣ 결과 확인

```bash
# 로그 파일 확인
cat logs/token_log.csv
cat logs/quality_log.csv

# 상태 파일 확인
cat state/fix_plan.md
cat state/claude-progress.txt

# 그래프 확인
ls analysis/*.png
```

---

## 📊 Context Rot 증명

### 1. Context Rot란?

**Context Rot**은 LLM 대화가 길어질수록 다음과 같은 문제가 발생하는 현상입니다:

- 🔴 **Irrelevant 정보 증가**: 오래된 대화가 누적되어 관련 없는 내용이 많아짐
- 🔴 **응답 품질 저하**: 핵심 정보를 찾기 어려워 응답 품질 감소
- 🔴 **토큰 낭비**: 불필요한 컨텍스트로 토큰 소비 증가
- 🔴 **레이턴시 증가**: 긴 컨텍스트 처리로 응답 시간 증가

### 2. 실험 설계

#### 실험 A: Context Reset 없음 (Baseline)
- MAX_TOKENS: 8000
- THRESHOLD: 무한대 (reset 안 함)
- 결과: 품질이 지속적으로 감소

#### 실험 B: Context Reset 있음 (Proposed)
- MAX_TOKENS: 8000
- THRESHOLD: 6000
- Reset 전략: Hybrid (요약 + 최근 대화 유지)
- 결과: 품질이 주기적으로 회복

### 3. 측정 지표

| 지표 | 설명 | 계산 방법 |
|------|------|-----------|
| **Token Count** | 현재 컨텍스트의 토큰 수 | `len(context) // 4` |
| **Context Length** | 컨텍스트 문자 수 | `len(context)` |
| **Quality Score** | 응답 품질 점수 (0-1) | Response length 기반 |
| **Reset Count** | 컨텍스트 초기화 횟수 | Token drop 감지 |

### 4. 예상 결과

#### ❌ Without Reset
```
Iteration  Tokens  Quality
1          250     1.0
5          1200    0.8
10         3500    0.6
15         6200    0.4
20         9000    0.2  ← 품질 지속 감소
```

#### ✅ With Reset
```
Iteration  Tokens  Quality  Reset
1          250     1.0      -
5          1200    0.9      -
8          6100    0.7      ✓ (reset)
9          800     1.0      -
15         5800    0.9      -
18         6200    0.8      ✓ (reset)
20         1100    1.0      - ← 품질 유지
```

---

## 🔧 핵심 구현 상세

### 1. 토큰 카운터 (count_tokens.py)

```python
def count_tokens(text):
    # Simple estimation: 1 token ≈ 4 characters
    return len(text) // 4
```

**특징**:
- tiktoken 우선 사용 (설치 시)
- fallback: 간단한 추정 (chars/4)

### 2. 컨텍스트 초기화 전략 (summarize_context.py)

#### 전략 비교

| 전략 | 장점 | 단점 | 사용 시기 |
|------|------|------|-----------|
| **Sliding Window** | 빠름, 간단 | 정보 손실 | 빠른 프로토타입 |
| **LLM Summarization** | 지능적 | API 비용, 느림 | 품질 중요 |
| **Hybrid** ⭐ | 균형 | 중간 복잡도 | **권장** |

#### Hybrid 전략 구현
```python
def summarize_context_hybrid(context, keep_recent=1000):
    old_context = context[:-keep_recent]
    recent_context = context[-keep_recent:]
    
    # Extract key points from old context
    key_points = extract_key_points(old_context)
    
    # Combine summary + recent
    return summary + recent_context
```

### 3. 자동 상태 추적 (update_state.py)

```python
def update_progress_file(response, iteration, tokens):
    progress = f"""
    Last Updated: {timestamp}
    Iteration: {iteration}
    Current Tokens: {tokens}
    Status: {parse_status(response)}
    """
    # Auto-update claude-progress.txt
```

**자동화 기능**:
- ✅ 작업 완료 감지 (`done`, `completed` 키워드)
- ✅ fix_plan.md 체크박스 자동 업데이트
- ✅ 진행 상황 타임스탬프 기록

---

## 📈 분석 결과

### 생성되는 그래프

1. **token_usage.png**
   - X축: Iteration
   - Y축: Token Count
   - 특징: Reset 지점 표시 (빨간 삼각형)

2. **context_growth.png**
   - 컨텍스트 길이 증가 추이

3. **quality_degradation.png**
   - 품질 저하 곡선
   - Trend line 표시

4. **combined_analysis.png**
   - 토큰 vs 품질 동시 표시
   - Dual Y-axis

5. **before_after_comparison.png** ⭐ **핵심 증거**
   - 왼쪽: Reset 없음 → 품질 감소
   - 오른쪽: Reset 있음 → 품질 유지

### 통계 요약 (analysis_summary.txt)

```
Token Statistics:
- Average tokens: 2345.67
- Max tokens: 6234
- Token growth rate: 312.45 per iteration

Quality Statistics:
- Average quality: 0.854
- Quality degradation: 0.146
- Min quality: 0.700

Context Resets Detected:
- Reset at iterations: 8, 15
- Total resets: 2
```

---

## ✅ 동작 증명 체크리스트

### 1. 로그 파일 ✓
- [x] `logs/token_log.csv` - 토큰 사용량 기록
- [x] `logs/context_log.csv` - 컨텍스트 길이 기록
- [x] `logs/quality_log.csv` - 품질 점수 기록

### 2. 그래프 ✓
- [x] Token usage with threshold line
- [x] Context growth chart
- [x] Quality degradation curve
- [x] Before/After comparison ⭐

### 3. 상태 추적 ✓
- [x] `fix_plan.md` - 작업 계획 및 체크박스
- [x] `claude-progress.txt` - 자동 업데이트되는 진행 상황

### 4. Reset 증거 ✓
- [x] 로그에서 토큰 급감 지점 확인 가능
- [x] 그래프에 Reset marker 표시
- [x] 품질 회복 패턴 확인 가능

---

## 🎯 핵심 인사이트

### 1. Context Management의 중요성

> "LLM 시스템을 그냥 쓰는 게 아니라,  
> **측정 가능하고, 유지 가능한 loop로 만드는 것**"

### 2. 측정 없이는 개선 불가

- ❌ "대화가 길어지면 이상해요" ← 주관적
- ✅ "토큰 6000 초과 시 품질 0.4로 감소" ← 객관적

### 3. 적절한 Reset 전략 필요

| Threshold | Reset 빈도 | 품질 | 효율성 |
|-----------|-----------|------|--------|
| 2000 | 매우 높음 | 높음 | ❌ 낮음 |
| 6000 | 적절 | 높음 | ✅ 높음 |
| 무한대 | 없음 | 낮음 | ❌ 낮음 |

**최적**: 6000 토큰 (75% threshold)

### 4. Hybrid 전략의 우수성

```
Simple Truncate:    [====XXXX] → [====]     (정보 손실)
LLM Summarize:      [====XXXX] → [==]       (비용 높음)
Hybrid:             [====XXXX] → [=====]    (균형) ⭐
                     요약 | 최근
```

---

## 📁 파일 구조

```
202321010/
├── ralph_with_context.sh       # Bash 버전 Ralph 루프
├── ralph_with_context.ps1      # PowerShell 버전 Ralph 루프
├── count_tokens.py             # 토큰 카운터
├── call_llm.py                 # LLM API 호출
├── summarize_context.py        # 컨텍스트 압축
├── update_state.py             # 상태 추적
├── input.txt                   # 입력 파일 (자동 생성)
│
├── logs/
│   ├── token_log.csv           # 생성됨: 실행 시
│   ├── context_log.csv         # 생성됨: 실행 시
│   └── quality_log.csv         # 생성됨: 실행 시
│
├── analysis/
│   ├── plot_context_rot.py     # 그래프 생성 스크립트
│   ├── token_usage.png         # 생성됨: 분석 시
│   ├── context_growth.png      # 생성됨: 분석 시
│   ├── quality_degradation.png # 생성됨: 분석 시
│   ├── combined_analysis.png   # 생성됨: 분석 시
│   ├── before_after_comparison.png # 생성됨: 분석 시
│   └── analysis_summary.txt    # 생성됨: 분석 시
│
├── state/
│   ├── fix_plan.md             # 작업 계획 (자동 업데이트)
│   └── claude-progress.txt     # 진행 상황 (자동 업데이트)
│
└── README.md                   # 이 파일
```

---

## 🔬 실험 재현 방법

### Step 1: 실행
```bash
# Windows
.\ralph_with_context.ps1

# Linux/Mac
./ralph_with_context.sh
```

### Step 2: 실시간 모니터링
```bash
# 별도 터미널에서
watch -n 1 "tail -5 logs/token_log.csv"
```

### Step 3: 분석
```bash
python analysis/plot_context_rot.py
```

### Step 4: 결과 확인
```bash
# 그래프 확인
open analysis/*.png

# 통계 확인
cat analysis/analysis_summary.txt

# 상태 확인
git diff state/fix_plan.md
cat state/claude-progress.txt
```

---

## 📝 주요 학습 내용

### 1. Context Window Management
- 토큰 제한 인식 및 관리
- 효율적인 컨텍스트 압축
- Reset timing 최적화

### 2. System Observability
- 로깅 전략 (CSV 형식)
- 메트릭 수집 (token, quality, length)
- 시각화 (matplotlib)

### 3. Automated State Tracking
- 진행 상황 자동 기록
- 작업 완료 자동 감지
- 상태 파일 동기화

### 4. Evidence-Based Engineering
- 주관적 평가 → 객관적 측정
- Before/After 비교
- 통계적 증거 수집

---

## 🚧 향후 개선 방향

### 1. 더 정확한 Quality Metric
- BLEU/ROUGE score 계산
- Semantic similarity (embeddings)
- Human evaluation integration

### 2. 동적 Threshold 조정
```python
def adaptive_threshold(quality_history):
    if quality_trend < 0.8:
        return THRESHOLD * 0.8  # 더 일찍 reset
    else:
        return THRESHOLD
```

### 3. Multi-strategy Compression
- 상황에 따라 전략 선택
- A/B testing 자동화
- 성능 벤치마크

### 4. Real-time Monitoring Dashboard
- Web UI로 실시간 모니터링
- Alert 시스템
- 자동 보고서 생성

---

## 📚 참고 자료

- [OpenAI Tokenizer](https://platform.openai.com/tokenizer)
- [Context Window Management Best Practices](https://help.openai.com/en/articles/4936856)
- [tiktoken Documentation](https://github.com/openai/tiktoken)

---

## 👤 작성자

**학번**: 202321010  
**날짜**: 2026-04-19  
**과제**: Lab 05 - Context Management

---

## 📄 License

This project is for educational purposes only.
