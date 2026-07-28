# NeuroLearn — Django Adaptive Learning Backend

## Thesis Defense Setup & Seeding

Before defense: run `python manage.py seed_thesis_demo` to reset to a clean, presentable demo state.

```bash
# Activate virtual environment
source venv/bin/activate

# Seed/reset thesis demo state (MPTT curriculum, DAG prerequisite convergence, BKT/IRT history curves)
python manage.py seed_thesis_demo
```

### Demo Credentials:
- **Demo Student (High Mastery & DAG Unlocked)**: `hybrid_demo@test.com` / `!2345678` (Completed Binary Trees & Graph Traversals; Demo Topic unlocked)
- **Secondary Student (Mixed Mastery Trajectory)**: `yuta@gmail.com` / `password123` (Moderate accuracy across trees & graphs)
- **Third Student (Low Mastery / Novice Trajectory)**: `alex@neuro.learn` / `password123` (Lower accuracy on fundamental CS & Data Structures)

### DAG Dependency Convergence Node:
- **Topic**: `Demo Topic` (Node ID 28)
- **Prerequisites**: Converges from `Binary Trees` (Data Structures branch) AND `Graph Traversals` (Algorithms branch).

### Active Student Engine:
- Configured in `config/settings.py` via `STUDENT_MODEL_ENGINE = "hybrid_bkt_irt"`.
