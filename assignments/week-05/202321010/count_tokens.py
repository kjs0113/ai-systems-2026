#!/usr/bin/env python3
"""
Token counter for context management
Estimates token count using simple heuristics (chars/4)
For more accurate counting, consider using tiktoken library
"""
import sys

def count_tokens(text):
    """
    Simple token estimation: ~4 characters per token
    For more accuracy, use: pip install tiktoken
    """
    if not text:
        return 0
    
    # Simple estimation: 1 token ≈ 4 characters
    # This is a rough approximation for English text
    return len(text) // 4

def count_tokens_accurate(text, model="gpt-3.5-turbo"):
    """
    Accurate token counting using tiktoken
    Uncomment this if tiktoken is installed
    """
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except ImportError:
        # Fallback to simple estimation
        return count_tokens(text)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("0")
        sys.exit(0)
    
    context = sys.argv[1]
    
    # Try accurate counting first, fallback to simple
    try:
        token_count = count_tokens_accurate(context)
    except:
        token_count = count_tokens(context)
    
    print(token_count)
