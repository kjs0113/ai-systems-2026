#!/usr/bin/env python3
"""
Context Rot Visualization
Generates graphs showing context growth, token usage, and quality degradation
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Directories
LOG_DIR = "logs"
OUTPUT_DIR = "analysis"

# Log files
TOKEN_LOG = os.path.join(LOG_DIR, "token_log.csv")
CONTEXT_LOG = os.path.join(LOG_DIR, "context_log.csv")
QUALITY_LOG = os.path.join(LOG_DIR, "quality_log.csv")

def load_logs():
    """Load all log files"""
    try:
        df_tokens = pd.read_csv(TOKEN_LOG)
        df_context = pd.read_csv(CONTEXT_LOG)
        df_quality = pd.read_csv(QUALITY_LOG)
        return df_tokens, df_context, df_quality
    except FileNotFoundError as e:
        print(f"Error: Log file not found - {e}")
        print("Please run ralph_with_context.sh first to generate logs.")
        return None, None, None

def plot_token_usage(df_tokens):
    """Plot token usage over iterations with threshold line"""
    plt.figure(figsize=(12, 6))
    
    plt.plot(df_tokens['iteration'], df_tokens['tokens'], 
             marker='o', linewidth=2, markersize=6, label='Token Count')
    
    # Add threshold line
    plt.axhline(y=6000, color='r', linestyle='--', 
                linewidth=2, label='Reset Threshold (6000)')
    
    # Highlight reset points (where tokens drop)
    resets = []
    for i in range(1, len(df_tokens)):
        if df_tokens.iloc[i]['tokens'] < df_tokens.iloc[i-1]['tokens'] * 0.7:
            resets.append(i)
    
    if resets:
        plt.scatter(df_tokens.iloc[resets]['iteration'], 
                   df_tokens.iloc[resets]['tokens'],
                   color='red', s=200, marker='v', 
                   label='Context Reset', zorder=5)
    
    plt.xlabel('Iteration', fontsize=12)
    plt.ylabel('Token Count', fontsize=12)
    plt.title('Token Usage Over Time (Context Rot Demonstration)', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, 'token_usage.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()

def plot_context_growth(df_context):
    """Plot context length growth"""
    plt.figure(figsize=(12, 6))
    
    plt.plot(df_context['iteration'], df_context['context_chars'], 
             marker='s', linewidth=2, markersize=6, color='green', label='Context Length (chars)')
    
    plt.xlabel('Iteration', fontsize=12)
    plt.ylabel('Context Length (characters)', fontsize=12)
    plt.title('Context Growth Over Iterations', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, 'context_growth.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()

def plot_quality_degradation(df_quality):
    """Plot quality score degradation (Context Rot effect)"""
    plt.figure(figsize=(12, 6))
    
    plt.plot(df_quality['iteration'], df_quality['quality_score'], 
             marker='D', linewidth=2, markersize=6, color='orange', label='Quality Score')
    
    # Add trend line
    z = np.polyfit(df_quality['iteration'], df_quality['quality_score'], 2)
    p = np.poly1d(z)
    plt.plot(df_quality['iteration'], p(df_quality['iteration']), 
             "--", color='red', linewidth=2, alpha=0.7, label='Trend')
    
    plt.xlabel('Iteration', fontsize=12)
    plt.ylabel('Quality Score', fontsize=12)
    plt.title('Response Quality Degradation (Context Rot)', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 1.1)
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, 'quality_degradation.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()

def plot_combined_analysis(df_tokens, df_quality):
    """Combined plot: tokens vs quality"""
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    # Token plot
    color = 'tab:blue'
    ax1.set_xlabel('Iteration', fontsize=12)
    ax1.set_ylabel('Token Count', color=color, fontsize=12)
    line1 = ax1.plot(df_tokens['iteration'], df_tokens['tokens'], 
                     marker='o', color=color, linewidth=2, label='Tokens')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.axhline(y=6000, color='gray', linestyle=':', alpha=0.5)
    ax1.grid(True, alpha=0.3)
    
    # Quality plot
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Quality Score', color=color, fontsize=12)
    line2 = ax2.plot(df_quality['iteration'], df_quality['quality_score'], 
                     marker='s', color=color, linewidth=2, label='Quality')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 1.1)
    
    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', fontsize=10)
    
    plt.title('Context Rot: Token Growth vs Quality Degradation', 
              fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, 'combined_analysis.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()

def plot_before_after_comparison():
    """
    Create a comparison showing:
    - Left: Without reset (quality degrades)
    - Right: With reset (quality maintained)
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Simulated data for "without reset"
    iterations_no_reset = list(range(1, 21))
    quality_no_reset = [1.0 - i*0.04 for i in range(20)]  # Linear degradation
    
    # Simulated data for "with reset"
    quality_with_reset = [1.0, 0.96, 0.92, 0.98, 1.0, 0.96, 0.92, 0.98, 
                          1.0, 0.96, 0.92, 0.98, 1.0, 0.96, 0.92, 0.98,
                          1.0, 0.96, 0.92, 0.98]  # Periodic recovery
    
    # Left plot: Without reset
    ax1.plot(iterations_no_reset, quality_no_reset, 
             marker='o', linewidth=2, color='red', label='Quality')
    ax1.set_xlabel('Iteration', fontsize=12)
    ax1.set_ylabel('Quality Score', fontsize=12)
    ax1.set_title('WITHOUT Context Reset\n(Context Rot Degrades Quality)', 
                  fontsize=12, fontweight='bold', color='red')
    ax1.set_ylim(0, 1.1)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Right plot: With reset
    ax2.plot(iterations_no_reset, quality_with_reset, 
             marker='s', linewidth=2, color='green', label='Quality')
    
    # Mark reset points
    reset_points = [3, 7, 11, 15, 19]
    ax2.scatter([i+1 for i in reset_points], 
               [quality_with_reset[i] for i in reset_points],
               color='blue', s=200, marker='v', label='Reset', zorder=5)
    
    ax2.set_xlabel('Iteration', fontsize=12)
    ax2.set_ylabel('Quality Score', fontsize=12)
    ax2.set_title('WITH Context Reset\n(Quality Maintained)', 
                  fontsize=12, fontweight='bold', color='green')
    ax2.set_ylim(0, 1.1)
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, 'before_after_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()

def generate_summary_stats(df_tokens, df_context, df_quality):
    """Generate summary statistics"""
    summary = f"""
=== Context Rot Analysis Summary ===

Token Statistics:
- Average tokens: {df_tokens['tokens'].mean():.2f}
- Max tokens: {df_tokens['tokens'].max()}
- Min tokens: {df_tokens['tokens'].min()}
- Token growth rate: {(df_tokens['tokens'].iloc[-1] - df_tokens['tokens'].iloc[0]) / len(df_tokens):.2f} per iteration

Context Statistics:
- Average context length: {df_context['context_chars'].mean():.2f} chars
- Max context length: {df_context['context_chars'].max()} chars
- Final context length: {df_context['context_chars'].iloc[-1]} chars

Quality Statistics:
- Average quality: {df_quality['quality_score'].mean():.3f}
- Quality degradation: {df_quality['quality_score'].iloc[0] - df_quality['quality_score'].mean():.3f}
- Min quality: {df_quality['quality_score'].min():.3f}

Context Resets Detected:
"""
    
    # Detect resets
    resets = []
    for i in range(1, len(df_tokens)):
        if df_tokens.iloc[i]['tokens'] < df_tokens.iloc[i-1]['tokens'] * 0.7:
            resets.append(i+1)
    
    if resets:
        summary += f"- Reset at iterations: {', '.join(map(str, resets))}\n"
        summary += f"- Total resets: {len(resets)}\n"
    else:
        summary += "- No resets detected\n"
    
    # Save summary
    summary_path = os.path.join(OUTPUT_DIR, 'analysis_summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(summary)
    print(f"✓ Saved: {summary_path}")

def main():
    """Main analysis function"""
    print("=== Context Rot Analysis ===\n")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load data
    print("Loading log files...")
    df_tokens, df_context, df_quality = load_logs()
    
    if df_tokens is None:
        return
    
    print(f"Loaded {len(df_tokens)} data points\n")
    
    # Import numpy for trend line
    global np
    import numpy as np
    
    # Generate plots
    print("Generating plots...")
    plot_token_usage(df_tokens)
    plot_context_growth(df_context)
    plot_quality_degradation(df_quality)
    plot_combined_analysis(df_tokens, df_quality)
    plot_before_after_comparison()
    
    # Generate summary
    print("\nGenerating summary statistics...")
    generate_summary_stats(df_tokens, df_context, df_quality)
    
    print("\n✓ Analysis complete!")
    print(f"All results saved in '{OUTPUT_DIR}/' directory")

if __name__ == "__main__":
    main()
