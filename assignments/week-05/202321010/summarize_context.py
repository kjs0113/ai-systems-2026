#!/usr/bin/env python3
"""
Context summarization and compression
Implements intelligent context reset strategies
"""
import sys
import re
from datetime import datetime

def sliding_window_compress(context, window_size=2000):
    """
    Keep only the most recent N characters
    Simple but loses historical context
    """
    return context[-window_size:]

def extract_key_points(context):
    """
    Extract key information from context
    Looks for important patterns and facts
    """
    key_points = []
    
    # Extract numbered items
    numbered_items = re.findall(r'\d+\.\s+([^\n]+)', context)
    key_points.extend(numbered_items[:5])  # Keep top 5
    
    # Extract questions
    questions = re.findall(r'[?][^\n]+', context)
    key_points.extend(questions[-3:])  # Keep last 3 questions
    
    # Extract AI responses (mock pattern)
    responses = re.findall(r'AI:\s*([^\n]+)', context)
    key_points.extend(responses[-3:])  # Keep last 3 AI responses
    
    return key_points

def summarize_context_hybrid(context, keep_recent=1000):
    """
    Hybrid approach (RECOMMENDED):
    - Summarize old context
    - Keep recent context verbatim
    """
    if len(context) <= keep_recent:
        return context
    
    # Split into old and recent
    old_context = context[:-keep_recent]
    recent_context = context[-keep_recent:]
    
    # Extract key points from old context
    key_points = extract_key_points(old_context)
    
    # Build summary
    summary = "=== Context Summary ===\n"
    summary += "Key points from earlier conversation:\n"
    for i, point in enumerate(key_points, 1):
        summary += f"{i}. {point}\n"
    
    summary += "\n=== Recent Context ===\n"
    summary += recent_context
    
    return summary

def summarize_context_llm(context):
    """
    Use LLM to summarize (most intelligent but requires API call)
    Falls back to hybrid if LLM unavailable
    """
    try:
        import subprocess
        
        prompt = f"Summarize the following conversation, keeping only the most important information:\n\n{context}"
        
        result = subprocess.run(
            ['python3', 'call_llm.py', prompt],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return summarize_context_hybrid(context)
    
    except Exception as e:
        return summarize_context_hybrid(context)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: No context provided")
        sys.exit(1)
    
    context = sys.argv[1]
    strategy = sys.argv[2] if len(sys.argv) > 2 else "hybrid"
    
    if strategy == "sliding":
        compressed = sliding_window_compress(context)
    elif strategy == "llm":
        compressed = summarize_context_llm(context)
    else:  # hybrid (default)
        compressed = summarize_context_hybrid(context)
    
    print(compressed)
