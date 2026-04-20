# Quick Start Guide

## 빠른 실행 (3단계)

### 1️⃣ 패키지 설치
```bash
pip install -r requirements.txt
```

### 2️⃣ Ralph 루프 실행

**Windows:**
```powershell
python -c "exec(open('ralph_with_context.ps1').read().replace('python3', 'python'))"
```
또는 Git Bash에서:
```bash
bash ralph_with_context.sh
```

**Linux/Mac:**
```bash
chmod +x ralph_with_context.sh
./ralph_with_context.sh
```

### 3️⃣ 그래프 생성
```bash
python analysis/plot_context_rot.py
```

---

## 실행 중 확인할 것

### ✅ 체크포인트

1. **Iteration 1-5**: 토큰이 서서히 증가
   ```
   Current tokens: 250
   Current tokens: 650
   Current tokens: 1200
   ```

2. **Iteration 8-10**: 첫 번째 Reset 발생 예상
   ```
   ⚠ Context threshold exceeded! Applying reset...
   ✓ Context compressed: 6234 → 987 tokens
   ```

3. **로그 파일 생성 확인**
   ```bash
   ls logs/
   # token_log.csv
   # context_log.csv
   # quality_log.csv
   ```

4. **상태 파일 업데이트 확인**
   ```bash
   cat state/claude-progress.txt
   ```

---

## 문제 해결

### Python3 vs Python
Windows에서 `python3` 명령을 찾을 수 없는 경우:

**방법 1**: Python 실행 파일 수정
```bash
# ralph_with_context.sh 파일에서
# python3 → python 으로 변경
```

**방법 2**: PowerShell 버전 사용
```powershell
.\ralph_with_context.ps1
```

### Git Bash 사용 (Windows 권장)
```bash
# Git Bash 설치 후
bash ralph_with_context.sh
```

### 그래프가 생성되지 않는 경우
```bash
# matplotlib 백엔드 확인
python -c "import matplotlib; print(matplotlib.get_backend())"

# Agg 백엔드로 변경 (GUI 없이 저장만)
# plot_context_rot.py 첫 줄에 추가:
# import matplotlib
# matplotlib.use('Agg')
```

---

## 실행 결과 확인

### 1. 로그 파일 내용 확인
```bash
# Windows
type logs\token_log.csv

# Linux/Mac
cat logs/token_log.csv
```

### 2. 그래프 확인
```bash
# Windows
explorer analysis\

# Linux/Mac
open analysis/
```

### 3. 통계 요약
```bash
cat analysis/analysis_summary.txt
```

---

## 예상 실행 시간

- Ralph 루프 (20 iterations): ~30초
- 그래프 생성: ~5초
- **총 소요 시간**: < 1분

---

## Mock vs Real API

### Mock Mode (기본값)
- API 키 불필요
- Context Rot 시뮬레이션 내장
- 품질 저하 패턴 자동 생성

### Real API Mode
```bash
# OpenAI API 키 설정
export OPENAI_API_KEY="sk-..."

# Windows
$env:OPENAI_API_KEY="sk-..."

# 실행 (자동으로 Real API 사용)
./ralph_with_context.sh
```

---

## 다음 단계

실행이 완료되면:

1. ✅ `analysis/` 폴더의 그래프 확인
2. ✅ `README.md`의 "동작 증명" 섹션 확인
3. ✅ `state/fix_plan.md`의 체크박스 확인
4. ✅ 실험 결과를 보고서에 포함

**핵심 증거**: `analysis/before_after_comparison.png` 그래프!
