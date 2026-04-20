#!/usr/bin/env python3
"""
State tracking system
Updates fix_plan.md and claude-progress.txt
"""
import sys
import os
import re
from datetime import datetime

STATE_DIR = "state"
FIX_PLAN_FILE = os.path.join(STATE_DIR, "fix_plan.md")
PROGRESS_FILE = os.path.join(STATE_DIR, "claude-progress.txt")

def parse_response_for_completion(response):
    """
    Detect task completion signals in LLM response
    """
    completion_signals = [
        "completed",
        "done",
        "finished",
        "implemented",
        "success",
        "working"
    ]
    
    for signal in completion_signals:
        if signal.lower() in response.lower():
            return True
    return False

def extract_task_from_response(response):
    """
    Try to extract what task was completed
    """
    # Look for patterns like "completed X" or "implemented Y"
    match = re.search(r'(completed|implemented|finished)\s+([^\n.]+)', response, re.IGNORECASE)
    if match:
        return match.group(2).strip()
    return "unknown task"

def update_fix_plan(task_description):
    """
    Mark task as done in fix_plan.md
    """
    if not os.path.exists(FIX_PLAN_FILE):
        return False
    
    try:
        with open(FIX_PLAN_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the task and mark it as done
        # Pattern: - [ ] task_description
        pattern = r'- \[ \]\s*' + re.escape(task_description[:30])
        replacement = f'- [x] {task_description[:30]}'
        
        # Also try generic pattern matching
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            if '- [ ]' in line and any(word in line.lower() for word in task_description.lower().split()[:3]):
                line = line.replace('- [ ]', '- [x]')
            updated_lines.append(line)
        
        with open(FIX_PLAN_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        return True
    
    except Exception as e:
        print(f"Error updating fix_plan: {e}", file=sys.stderr)
        return False

def update_progress_file(response, iteration, tokens):
    """
    Update claude-progress.txt with current state
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine current task
        if parse_response_for_completion(response):
            current_task = extract_task_from_response(response)
            status = "Task completed"
        else:
            current_task = "In progress"
            status = "Working"
        
        # Build progress summary
        progress = f"""=== Ralph Loop Progress ===
Last Updated: {timestamp}
Iteration: {iteration}
Current Tokens: {tokens}
Status: {status}
Last Task: {current_task}

Last Response Preview:
{response[:200]}...

Next Steps:
- Continue monitoring context growth
- Apply reset if needed
- Track quality metrics
"""
        
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            f.write(progress)
        
        return True
    
    except Exception as e:
        print(f"Error updating progress: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: No response provided")
        sys.exit(1)
    
    response = sys.argv[1]
    iteration = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    tokens = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    
    # Update progress file
    update_progress_file(response, iteration, tokens)
    
    # Update fix plan if task completed
    if parse_response_for_completion(response):
        task = extract_task_from_response(response)
        update_fix_plan(task)
        print(f"Task marked as completed: {task}")
    else:
        print("Progress updated")
