#!/bin/bash
# Linux/Mac용 빠른 실행 스크립트

echo "============================================"
echo "Lab 05: Context Management - Quick Run"
echo "============================================"
echo ""

# 1. 패키지 확인
echo "[1/3] Checking Python packages..."
if python3 -c "import pandas, matplotlib, numpy" 2>/dev/null; then
    echo "✓ Packages OK!"
else
    echo "Installing required packages..."
    pip3 install -r requirements.txt
fi
echo ""

# 2. Ralph 루프 실행
echo "[2/3] Running Ralph Loop..."
echo "This will take about 30 seconds..."
echo ""

chmod +x ralph_with_context.sh
./ralph_with_context.sh

echo ""
echo "✓ Ralph Loop completed!"
echo ""

# 3. 그래프 생성
echo "[3/3] Generating graphs..."
python3 analysis/plot_context_rot.py

echo ""
echo "============================================"
echo "✓ DONE! Check the results:"
echo "============================================"
echo ""
echo "1. Logs: logs/*.csv"
echo "2. Graphs: analysis/*.png"
echo "3. Summary: analysis/analysis_summary.txt"
echo "4. State: state/claude-progress.txt"
echo ""
echo "🎯 Key Evidence: analysis/before_after_comparison.png"
echo ""
