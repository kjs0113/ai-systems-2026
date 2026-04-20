@echo off
REM Windows용 빠른 실행 스크립트

echo ============================================
echo Lab 05: Context Management - Quick Run
echo ============================================
echo.

REM 1. 패키지 확인
echo [1/3] Checking Python packages...
python -c "import pandas, matplotlib, numpy" 2>nul
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
) else (
    echo Packages OK!
)
echo.

REM 2. Ralph 루프 실행
echo [2/3] Running Ralph Loop...
echo This will take about 30 seconds...
echo.
python -c "exec(\"\"\"import subprocess; import os; os.chdir('d:/ai-systems-2026/assignments/week-05/202321010'); exec(open('ralph_with_context.ps1').read().replace('python3', 'python').replace('Write-Host', 'print').replace('-ForegroundColor Green', '').replace('-ForegroundColor Yellow', '').replace('-ForegroundColor Red', ''))\"\"\")" 2>nul

if errorlevel 1 (
    echo Falling back to PowerShell version...
    powershell -ExecutionPolicy Bypass -File ralph_with_context.ps1
)

echo.
echo Ralph Loop completed!
echo.

REM 3. 그래프 생성
echo [3/3] Generating graphs...
python analysis\plot_context_rot.py

echo.
echo ============================================
echo DONE! Check the results:
echo ============================================
echo.
echo 1. Logs: logs\*.csv
echo 2. Graphs: analysis\*.png
echo 3. Summary: analysis\analysis_summary.txt
echo 4. State: state\claude-progress.txt
echo.
echo Key Evidence: analysis\before_after_comparison.png
echo.

pause
