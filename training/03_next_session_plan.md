# Next Session Plan - ML Chess Engine Implementation

## Current Status
- Design document complete for sections 3 (Features), 4 (Model 1), 6 (RL)
- Sections still placeholder: 1, 2, 5, 7, 8, 9, 10

## Priority for Next Session

### 1. Complete Data Section (Section 2)
- Define exact data structure for training records
- Decide on storage format (JSON, CSV, pickle?)
- Plan data generation pipeline

### 2. Feature Extraction Code
- Review engine5 to identify existing features
- Create `feature_extractor.py`:
  - Extract features from chess.Board
  - Return feature vector
- Start with core features:
  - Material counts
  - Piece mobility
  - King safety basics
  - Pawn structure

### 3. Basic Training Infrastructure
- Create `training/` code structure:
  ```
  training/
    data/           # game data storage
    models/         # saved models
    src/
      feature_extractor.py
      data_collector.py
      critic_model.py
      actor_model.py
      trainer.py
  ```

### 4. Simple Critic Model (Proof of Concept)
- Gradient Boosting model for position evaluation
- Train on small dataset (~100 games)
- Test: does it learn that more material = better?

### 5. Integration Test
- Create simple ML engine that uses Critic for evaluation
- Run tournament against random engine
- Verify it beats random consistently

## Questions to Resolve
- [ ] Which features to implement first?
- [ ] How to represent moves as features for Actor?
- [ ] Storage format for game data?
- [ ] How many games for initial training?

## Dependencies
- scikit-learn (for Gradient Boosting)
- python-chess (already in project)
- numpy

## Success Criteria for Next Session
1. Feature extractor working
2. Data collection pipeline working
3. Critic model trained on sample data
4. ML engine beats random engine >80%
