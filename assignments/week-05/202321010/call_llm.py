#!/usr/bin/env python3
"""
LLM API caller with support for OpenAI and mock mode
"""
import sys
import os
import json
import time
from datetime import datetime

def call_openai(prompt, api_key=None, model="gpt-3.5-turbo"):
    """
    Call OpenAI API
    Requires: pip install openai
    """
    try:
        import openai
        
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai.api_key:
            raise ValueError("No API key provided")
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        # Fallback to mock if API fails
        return call_mock(prompt)

def call_mock(prompt):
    """
    Mock LLM response for testing without API
    Simulates degradation with context length
    """
    # Extract context length indicator if present
    context_length = len(prompt)
    
    # Simulate context rot: longer context = worse quality
    if context_length < 1000:
        quality = "high"
        response = f"[Mock Response - High Quality] I understand your request clearly. Context is fresh."
    elif context_length < 3000:
        quality = "medium"
        response = f"[Mock Response - Medium Quality] I think I understand, but context is getting long..."
    else:
        quality = "low"
        response = f"[Mock Response - Low Quality] I'm not sure what you're asking. Too much context noise."
    
    # Add some variation
    timestamp = datetime.now().strftime("%H:%M:%S")
    response += f"\n[Time: {timestamp}, Context Length: {context_length}, Quality: {quality}]"
    
    return response

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: No prompt provided")
        sys.exit(1)
    
    prompt = sys.argv[1]
    
    # Check for API key
    use_real_api = os.getenv("OPENAI_API_KEY") is not None
    
    if use_real_api:
        try:
            response = call_openai(prompt)
        except:
            # Fallback to mock
            response = call_mock(prompt)
    else:
        # Use mock mode
        response = call_mock(prompt)
    
    print(response)
