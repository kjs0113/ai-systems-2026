#!/bin/bash
# ralph_with_context.sh
# Ralph loop with context management and token tracking

# Configuration
MAX_TOKENS=8000
THRESHOLD=6000
MAX_ITERATIONS=20
CONTEXT=""
ITERATION=0

# Directories
LOG_DIR="logs"
STATE_DIR="state"

# Log files
TOKEN_LOG="$LOG_DIR/token_log.csv"
CONTEXT_LOG="$LOG_DIR/context_log.csv"
QUALITY_LOG="$LOG_DIR/quality_log.csv"

# Input file
INPUT_FILE="input.txt"

# Initialize log files
echo "timestamp,iteration,tokens,context_length" > "$TOKEN_LOG"
echo "timestamp,iteration,context_chars,context_lines" > "$CONTEXT_LOG"
echo "timestamp,iteration,quality_score,response_length" > "$QUALITY_LOG"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Ralph Loop with Context Management ===${NC}"
echo "Max Tokens: $MAX_TOKENS"
echo "Reset Threshold: $THRESHOLD"
echo "Max Iterations: $MAX_ITERATIONS"
echo ""

# Main loop
while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    ITERATION=$((ITERATION + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${GREEN}--- Iteration $ITERATION ---${NC}"
    
    # Read input
    if [ ! -f "$INPUT_FILE" ]; then
        echo -e "${YELLOW}Creating default input file...${NC}"
        echo "What is artificial intelligence?" > "$INPUT_FILE"
    fi
    
    INPUT=$(cat "$INPUT_FILE")
    echo "Input: $INPUT"
    
    # Calculate current token count
    TOKENS=$(python3 count_tokens.py "$CONTEXT")
    CONTEXT_LENGTH=${#CONTEXT}
    
    echo "Current tokens: $TOKENS"
    echo "Context length: $CONTEXT_LENGTH chars"
    
    # Check if context reset is needed
    if [ "$TOKENS" -gt "$THRESHOLD" ]; then
        echo -e "${RED}⚠ Context threshold exceeded! Applying reset...${NC}"
        
        # Apply summarization (hybrid strategy)
        CONTEXT=$(python3 summarize_context.py "$CONTEXT" "hybrid")
        
        NEW_TOKENS=$(python3 count_tokens.py "$CONTEXT")
        echo -e "${GREEN}✓ Context compressed: $TOKENS → $NEW_TOKENS tokens${NC}"
        TOKENS=$NEW_TOKENS
    fi
    
    # Build prompt
    if [ -z "$CONTEXT" ]; then
        PROMPT="User: $INPUT"
    else
        PROMPT="$CONTEXT\nUser: $INPUT"
    fi
    
    # Call LLM
    echo "Calling LLM..."
    RESPONSE=$(python3 call_llm.py "$PROMPT")
    
    echo "Response: ${RESPONSE:0:100}..."
    
    # Update context
    CONTEXT="$CONTEXT\nUser: $INPUT\nAI: $RESPONSE"
    
    # Calculate metrics
    RESPONSE_LENGTH=${#RESPONSE}
    
    # Simple quality metric: longer response = better (for mock)
    # In real system, use BLEU/ROUGE or embedding similarity
    if [ $RESPONSE_LENGTH -gt 200 ]; then
        QUALITY=1.0
    elif [ $RESPONSE_LENGTH -gt 100 ]; then
        QUALITY=0.7
    else
        QUALITY=0.4
    fi
    
    # Log metrics
    echo "$TIMESTAMP,$ITERATION,$TOKENS,$CONTEXT_LENGTH" >> "$TOKEN_LOG"
    
    CONTEXT_LINES=$(echo -e "$CONTEXT" | wc -l)
    echo "$TIMESTAMP,$ITERATION,$CONTEXT_LENGTH,$CONTEXT_LINES" >> "$CONTEXT_LOG"
    
    echo "$TIMESTAMP,$ITERATION,$QUALITY,$RESPONSE_LENGTH" >> "$QUALITY_LOG"
    
    # Update state tracking
    python3 update_state.py "$RESPONSE" "$ITERATION" "$TOKENS"
    
    # Add noise to simulate context rot (every 3 iterations)
    if [ $((ITERATION % 3)) -eq 0 ]; then
        NOISE="[Noise added at iteration $ITERATION: random irrelevant information that degrades context quality and makes it harder for the model to extract relevant information]"
        CONTEXT="$CONTEXT\n$NOISE"
        echo -e "${YELLOW}+ Added context noise for simulation${NC}"
    fi
    
    echo ""
    
    # Sleep briefly to simulate real usage
    sleep 1
done

echo -e "${GREEN}=== Ralph Loop Completed ===${NC}"
echo "Total iterations: $ITERATION"
echo "Final context length: ${#CONTEXT} chars"
echo "Log files saved in $LOG_DIR/"
echo ""
echo "Run analysis: python3 analysis/plot_context_rot.py"
