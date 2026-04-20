# Fix Plan - Lab 05: Context Management

## 📋 Task List

### Phase 1: Core Infrastructure
- [x] Create directory structure (logs/, analysis/, state/)
- [x] Implement token counter (count_tokens.py)
- [x] Implement LLM caller (call_llm.py)
- [ ] Test token counting with sample text

### Phase 2: Context Management
- [x] Implement context summarization (summarize_context.py)
- [ ] Test sliding window strategy
- [ ] Test hybrid compression strategy
- [ ] Validate context reset logic

### Phase 3: Ralph Loop Integration
- [x] Build main Ralph loop (ralph_with_context.sh)
- [ ] Integrate token counter into loop
- [ ] Add context reset trigger
- [ ] Implement logging system
- [ ] Test end-to-end loop

### Phase 4: State Tracking
- [x] Implement state update system (update_state.py)
- [ ] Automatic task completion detection
- [ ] Progress file auto-update
- [ ] Test state tracking workflow

### Phase 5: Analysis & Visualization
- [x] Create plot generation script (plot_context_rot.py)
- [ ] Generate token usage graph
- [ ] Generate context growth graph
- [ ] Generate quality degradation graph
- [ ] Create before/after comparison

### Phase 6: Experimentation
- [ ] Run baseline experiment (no reset)
- [ ] Run experiment with context reset
- [ ] Collect evidence of context rot
- [ ] Document quality metrics
- [ ] Compare results

### Phase 7: Documentation
- [ ] Create comprehensive README
- [ ] Document experiment setup
- [ ] Include graph screenshots
- [ ] Add usage instructions
- [ ] Write conclusions

## 🎯 Current Focus
Implementing and testing the complete Ralph loop with context management.

## 📝 Notes
- Use mock LLM if no API key available
- Token estimation: ~4 chars per token
- Reset threshold: 6000 tokens
- Max context: 8000 tokens
- Hybrid compression: summarize old + keep recent

## ⚠️ Known Issues
- None yet

## ✅ Success Criteria
1. Ralph loop runs successfully for 20+ iterations
2. Context reset triggers automatically
3. Logs generated correctly (CSV format)
4. Graphs show clear context rot pattern
5. State files update automatically
6. Before/after quality difference visible
