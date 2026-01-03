# Claude Code Project Context

## Project: Chess Engine with ML Training

### Current State
Building ML-based chess engines using Reinforcement Learning with Actor-Critic architecture.

### Key Documents
- `training/02_design_document.md` - Full design (English)
- `training/02_design_document_hebrew.md` - Full design (Hebrew)
- `training/03_next_session_plan.md` - Next steps

### Architecture Decisions
- **Model 1 (Classical ML):** Two Gradient Boosting models (Actor + Critic)
- **Model 2 (Neural Network):** To be implemented after Model 1
- **RL Approach:** Actor-Critic with sparse rewards (game result only)
- **Features:** Extracted from engine5, no Stockfish evaluations (pure RL)

### Session End Protocol
Before ending any session:
1. Update design docs if decisions were made
2. Update `training/03_next_session_plan.md` with:
   - What was completed
   - Current state
   - Next steps
   - Open questions
3. Commit and push all changes

### Language Preference
- Code and technical docs: English
- Discussion: Hebrew or English (user preference)
- Design docs: Both languages, keep synchronized
