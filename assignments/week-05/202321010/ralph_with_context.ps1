# ralph_with_context.ps1
# Ralph loop with context management (PowerShell version for Windows)

# Configuration
$MAX_TOKENS = 8000
$THRESHOLD = 6000
$MAX_ITERATIONS = 20
$CONTEXT = ""
$ITERATION = 0

# Directories
$LOG_DIR = "logs"
$STATE_DIR = "state"

# Log files
$TOKEN_LOG = "$LOG_DIR/token_log.csv"
$CONTEXT_LOG = "$LOG_DIR/context_log.csv"
$QUALITY_LOG = "$LOG_DIR/quality_log.csv"

# Input file
$INPUT_FILE = "input.txt"

# Initialize log files
"timestamp,iteration,tokens,context_length" | Out-File -FilePath $TOKEN_LOG -Encoding utf8
"timestamp,iteration,context_chars,context_lines" | Out-File -FilePath $CONTEXT_LOG -Encoding utf8
"timestamp,iteration,quality_score,response_length" | Out-File -FilePath $QUALITY_LOG -Encoding utf8

Write-Host "=== Ralph Loop with Context Management ===" -ForegroundColor Green
Write-Host "Max Tokens: $MAX_TOKENS"
Write-Host "Reset Threshold: $THRESHOLD"
Write-Host "Max Iterations: $MAX_ITERATIONS"
Write-Host ""

# Main loop
while ($ITERATION -lt $MAX_ITERATIONS) {
    $ITERATION++
    $TIMESTAMP = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "--- Iteration $ITERATION ---" -ForegroundColor Green
    
    # Read input
    if (-not (Test-Path $INPUT_FILE)) {
        Write-Host "Creating default input file..." -ForegroundColor Yellow
        "What is artificial intelligence?" | Out-File -FilePath $INPUT_FILE -Encoding utf8
    }
    
    $INPUT = Get-Content $INPUT_FILE -Raw
    Write-Host "Input: $INPUT"
    
    # Calculate current token count
    $TOKENS = python count_tokens.py "$CONTEXT"
    $CONTEXT_LENGTH = $CONTEXT.Length
    
    Write-Host "Current tokens: $TOKENS"
    Write-Host "Context length: $CONTEXT_LENGTH chars"
    
    # Check if context reset is needed
    if ([int]$TOKENS -gt $THRESHOLD) {
        Write-Host "⚠ Context threshold exceeded! Applying reset..." -ForegroundColor Red
        
        # Apply summarization
        $CONTEXT = python summarize_context.py "$CONTEXT" "hybrid"
        
        $NEW_TOKENS = python count_tokens.py "$CONTEXT"
        Write-Host "✓ Context compressed: $TOKENS → $NEW_TOKENS tokens" -ForegroundColor Green
        $TOKENS = $NEW_TOKENS
    }
    
    # Build prompt
    if ([string]::IsNullOrEmpty($CONTEXT)) {
        $PROMPT = "User: $INPUT"
    } else {
        $PROMPT = "$CONTEXT`nUser: $INPUT"
    }
    
    # Call LLM
    Write-Host "Calling LLM..."
    $RESPONSE = python call_llm.py "$PROMPT"
    
    $ResponsePreview = if ($RESPONSE.Length -gt 100) { $RESPONSE.Substring(0, 100) } else { $RESPONSE }
    Write-Host "Response: $ResponsePreview..."
    
    # Update context
    $CONTEXT = "$CONTEXT`nUser: $INPUT`nAI: $RESPONSE"
    
    # Calculate metrics
    $RESPONSE_LENGTH = $RESPONSE.Length
    
    # Simple quality metric
    if ($RESPONSE_LENGTH -gt 200) {
        $QUALITY = 1.0
    } elseif ($RESPONSE_LENGTH -gt 100) {
        $QUALITY = 0.7
    } else {
        $QUALITY = 0.4
    }
    
    # Log metrics
    "$TIMESTAMP,$ITERATION,$TOKENS,$CONTEXT_LENGTH" | Out-File -Append -FilePath $TOKEN_LOG -Encoding utf8
    
    $CONTEXT_LINES = ($CONTEXT -split "`n").Count
    "$TIMESTAMP,$ITERATION,$CONTEXT_LENGTH,$CONTEXT_LINES" | Out-File -Append -FilePath $CONTEXT_LOG -Encoding utf8
    
    "$TIMESTAMP,$ITERATION,$QUALITY,$RESPONSE_LENGTH" | Out-File -Append -FilePath $QUALITY_LOG -Encoding utf8
    
    # Update state tracking
    python update_state.py "$RESPONSE" "$ITERATION" "$TOKENS"
    
    # Add noise to simulate context rot
    if ($ITERATION % 3 -eq 0) {
        $NOISE = "[Noise added at iteration $ITERATION : random irrelevant information that degrades context quality]"
        $CONTEXT = "$CONTEXT`n$NOISE"
        Write-Host "+ Added context noise for simulation" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Start-Sleep -Seconds 1
}

Write-Host "=== Ralph Loop Completed ===" -ForegroundColor Green
Write-Host "Total iterations: $ITERATION"
Write-Host "Final context length: $($CONTEXT.Length) chars"
Write-Host "Log files saved in $LOG_DIR/"
Write-Host ""
Write-Host "Run analysis: python analysis/plot_context_rot.py"
