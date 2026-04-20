# Week 05: Context Management & Token Optimization
Student ID: 202321006

## 1. Context Manager System
Implemented `context_manager.py` to handle dynamic context pruning and priority-based filtering.

## 2. Token Counter Implementation
`token_counter.py` provides accurate counting for Claude models, preventing overflow in long sessions.

## 3. Key Findings
- **Context Rot**: Mitigated by sliding window technique.
- **Dynamic Pruning**: High-priority blocks (errors, requirements) are preserved longer.
