"""
assessments/services/question_import.py — validated bulk import of questions.

Parsed records are checked before anything is written: the target must be an
active node of kind ``topic`` (Y4) and every question needs 2–4 choices with
exactly one correct answer (the ≤ 4 rule also holds on this bulk path). Errors
are reported per question and nothing is imported unless all records are valid.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from assessments.models import MAX_CHOICES, Choice, DifficultyLevel, Question


@dataclass(frozen=True)
class RecordError:
    question: int  # 1-based position of the record in the file
    message: str


class ImportRejected(Exception):
    def __init__(self, detail: str, errors: list[RecordError] | None = None, reason: str = "invalid"):
        super().__init__(detail)
        self.detail = detail
        self.errors = errors or []
        self.reason = reason

    def payload(self) -> dict:
        return {
            "detail": self.detail,
            "reason": self.reason,
            "errors": [{"question": e.question, "message": e.message} for e in self.errors],
        }


def validate_records(records: list[dict]) -> list[RecordError]:
    errors: list[RecordError] = []
    for number, record in enumerate(records, 1):
        choices = record.get("choices", [])
        if not str(record.get("text", "")).strip():
            errors.append(RecordError(number, "The question text is empty."))
        if not 2 <= len(choices) <= MAX_CHOICES:
            errors.append(RecordError(number, f"A question needs 2 to {MAX_CHOICES} options; found {len(choices)}."))
        if sum(1 for c in choices if c.get("is_correct")) != 1:
            errors.append(RecordError(number, "Exactly one option must be correct."))
        if any(not str(c.get("text", "")).strip() for c in choices):
            errors.append(RecordError(number, "An option is empty."))
        if record.get("difficulty") not in DifficultyLevel.values:
            errors.append(RecordError(number, f"Unknown difficulty {record.get('difficulty')!r}."))
    return errors


def import_questions(topic, records: list[dict]) -> int:
    """Create all questions or none; returns the number created."""
    if topic.kind != "topic" or topic.is_archived:
        raise ImportRejected(
            f"'{topic.name}' is a {topic.kind}; questions can only be imported into an active topic (Y4).",
            reason="y4",
        )
    errors = validate_records(records)
    if errors:
        raise ImportRejected("The file has invalid questions; nothing was imported.", errors)

    with transaction.atomic():
        questions = Question.objects.bulk_create([
            Question(
                topic=topic,
                text=record["text"],
                difficulty=record["difficulty"],
                explanation=record.get("explanation", ""),
                is_active=True,
            )
            for record in records
        ])
        Choice.objects.bulk_create([
            Choice(question=question, text=choice["text"], is_correct=choice["is_correct"])
            for question, record in zip(questions, records)
            for choice in record["choices"]
        ])
    return len(questions)
