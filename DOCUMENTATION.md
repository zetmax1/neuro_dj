# Adaptive Learning Platform — Full Technical Documentation

## 1. Project Overview
This project is a high-performance, strictly decoupled Django-based backend for an Adaptive Educational Platform. The system tracks user mastery on various subjects, adapts quiz difficulty based on their knowledge state, and maps out a hierarchical learning path using advanced SQL features.

---

## 2. Architecture & Domain Isolation

The project is split into two fully isolated Django apps. This enforces Domain Driven Design (DDD) and completely eradicates circular dependencies.

### Application Boundaries
1. **`curriculum` (Knowledge Base Structure)**
   - Responsible for the static, hierarchical tree of learning topics.
   - **Dependency Rule:** Never imports anything from `assessments`.

2. **`assessments` (Adaptive Engine & Tracking)**
   - Responsible for questions, choices, user attempts, and knowledge state tracking.
   - **Dependency Rule:** Allowed to depend on `curriculum`, but strictly uses string-based foreign keys (e.g., `models.ForeignKey("curriculum.Topic")`) to prevent import-level coupling.

### The "Thin Views, Fat Services" Pattern
All views in `views.py` are strictly responsible for:
1. HTTP Routing
2. Permission checking
3. Input validation
4. Serialization

All complex business logic lives in `services.py` modules. The views **never** construct complex ORM queries or perform state manipulations directly.

---

## 3. Data Models

### Curriculum App
- **`Topic`**: Represents a node in the learning path (e.g., Math -> Algebra). Built using `django-tree-queries` (`TreeNode`), which utilizes recursive CTEs (Common Table Expressions) for lightning-fast hierarchical traversal, completely bypassing the massive N+1 query problems associated with traditional Django hierarchies.

### Assessments App
- **`Question`**: Assessment content linked to a `Topic`. Includes a `difficulty` level (Easy=1, Medium=2, Hard=3) used by the adaptive engine.
- **`Choice`**: The answers for a question. Exactly one choice has `is_correct=True`.
- **`UserKnowledgeState`**: A unique constraint table linking a `User` to a `Topic`. Tracks `mastery_level`, `score` (accuracy %), and `streak` (consecutive correct answers).
- **`AssessmentAttempt`**: An immutable log of every choice a user submits, used for analytics and to prevent the engine from re-serving the exact same question.

---

## 4. The Adaptive State Machine Algorithm

Located in `assessments.services.process_submission`. The system uses a strict set of rules to govern how a user progresses.

### Promotion Rules
When a user submits a correct answer, their `streak` increments.
1. **Gradual Promotion:** If `streak >= 2` (STREAK_TO_PROMOTE), the user's `mastery_level` advances by 1 step (e.g., Beginner -> Intermediate) and the streak resets to 0.
2. **Fast-Track Mastery:** If the user gets `streak >= 3` on **HARD** difficulty questions, they instantly jump to `MASTERED`.

### Mastery Cascading
When a user reaches `MASTERED` on a parent topic, a downward cascade is triggered. The system runs an atomic bulk-upsert to automatically grant `MASTERED` status to **all descendant child topics** beneath it in the tree.

### Adaptive Question Selection
Located in `assessments.services.get_next_question`.
1. Look up user's `mastery_level` for the given topic.
2. Map mastery to target difficulty (Not Started/Beginner = Easy, Intermediate = Medium, Advanced/Mastered = Hard).
3. Exclude questions the user has already answered correctly.
4. Serve the first available question matching the target difficulty.

---

## 5. API Reference

All endpoints enforce **snake_case** for JSON payloads and require `IsAuthenticated`.

### A. Learning Path
**`GET /api/learning_path/tree/`**
- **Description**: Returns the full nested curriculum tree, annotated with the requesting user's mastery scores and unlock status.
- **Performance**: 1 DB query using `Subquery`, `OuterRef`, and in-memory Python tree construction.
- **Response**:
```json
[
  {
    "id": 1,
    "name": "Mathematics",
    "slug": "math",
    "parent_id": null,
    "mastery_percentage": 85,
    "mastery_level": 3,
    "mastery_level_display": "Advanced",
    "is_unlocked": true,
    "children": [
      {
        "id": 2,
        "name": "Algebra",
        "slug": "algebra",
        "parent_id": 1,
        // ... nested data
      }
    ]
  }
]
```

### B. Adaptive Assessments
**`GET /api/assessments/next_question/?topic_id=<int>`**
- **Description**: Returns the next question adapted to the user's current knowledge state.
- **Security**: The `is_correct` boolean and `explanation` text are strictly stripped from this payload.
- **Response**:
```json
{
  "id": 105,
  "text": "What is 2 + 2?",
  "difficulty": 1,
  "difficulty_display": "Easy",
  "topic_id": 2,
  "topic_name": "Algebra",
  "choices": [
    { "id": 401, "text": "3" },
    { "id": 402, "text": "4" }
  ]
}
```

**`POST /api/assessments/submit_answer/`**
- **Description**: Evaluates the user's answer, recalculates their streak/score, executes promotions, and seamlessly returns the next question.
- **Request**:
```json
{
  "question_id": 105,
  "choice_id": 402
}
```
- **Response**:
```json
{
  "is_correct": true,
  "explanation": "Because 2 plus 2 equals 4.",
  "mastery_level": 2,
  "mastery_display": "Intermediate",
  "streak": 1,
  "next_question": { 
     // Full Question object for immediate frontend rendering
  }
}
```

### C. Knowledge Tracking
**`GET /api/knowledge_states/`**
- **Description**: Returns a list of all topics the user has interacted with and their corresponding stats.

---

## 6. Technical Safeguards & Optimizations

1. **ACID Transactions (`@transaction.atomic`)**
   - The entire submission flow (logging attempt, locking knowledge state, cascading mastery) happens in a single transaction. If any step fails, the entire database rolls back.
2. **Concurrency Protections (`select_for_update`)**
   - When fetching the `UserKnowledgeState` during a submission, the database row is locked. This prevents a race condition where a user rapid-fires two requests and breaks the streak/score calculation.
3. **N+1 Query Elimination**
   - `select_related` is aggressively used to fetch `ForeignKey` objects (e.g., getting a Question's Topic).
   - `prefetch_related` combined with `Prefetch()` objects is aggressively used to fetch reverse-relations (e.g., getting a Question's Choices).
   - The tree building in `curriculum/serializers/topic.py` happens in `O(n)` time purely in Python via dictionary mapping.
