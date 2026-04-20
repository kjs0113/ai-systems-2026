#!/usr/bin/env python3
"""
Generate demo data for Context Rot visualization
(For demonstration without running full Ralph loop)
"""
import os
import pandas as pd
from datetime import datetime, timedelta

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Simulate 20 iterations with context growth and resets
iterations = list(range(1, 21))
base_time = datetime.now()

# Token data with resets at iterations 8 and 15
tokens = []
context_lengths = []
qualities = []

current_tokens = 200
current_context = 500

for i in iterations:
    # Context growth
    if i in [8, 15]:  # Reset points
        current_tokens = int(current_tokens * 0.15)  # Compress
        current_context = int(current_context * 0.2)
        quality = 1.0
    else:
        # Normal growth
        current_tokens += 300 + (i * 20)
        current_context += 800 + (i * 50)
        
        # Quality degrades with context length
        if current_tokens < 2000:
            quality = 1.0
        elif current_tokens < 4000:
            quality = 0.9
        elif current_tokens < 6000:
            quality = 0.7
        else:
            quality = 0.5
    
    tokens.append(current_tokens)
    context_lengths.append(current_context)
    qualities.append(quality)

# Create timestamps
timestamps = [(base_time + timedelta(seconds=i*2)).strftime("%Y-%m-%d %H:%M:%S") 
              for i in range(len(iterations))]

# Token log
df_tokens = pd.DataFrame({
    'timestamp': timestamps,
    'iteration': iterations,
    'tokens': tokens,
    'context_length': context_lengths
})
df_tokens.to_csv(os.path.join(LOG_DIR, 'token_log.csv'), index=False)

# Context log
df_context = pd.DataFrame({
    'timestamp': timestamps,
    'iteration': iterations,
    'context_chars': context_lengths,
    'context_lines': [i * 4 + 10 for i in iterations]
})
df_context.to_csv(os.path.join(LOG_DIR, 'context_log.csv'), index=False)

# Quality log
df_quality = pd.DataFrame({
    'timestamp': timestamps,
    'iteration': iterations,
    'quality_score': qualities,
    'response_length': [int(q * 200 + 50) for q in qualities]
})
df_quality.to_csv(os.path.join(LOG_DIR, 'quality_log.csv'), index=False)

print("✓ Demo data generated successfully!")
print(f"\nGenerated files:")
print(f"  - {LOG_DIR}/token_log.csv")
print(f"  - {LOG_DIR}/context_log.csv")
print(f"  - {LOG_DIR}/quality_log.csv")
print(f"\nResets detected at iterations: 8, 15")
print(f"Total iterations: {len(iterations)}")
print(f"\nRun: python analysis/plot_context_rot.py")
