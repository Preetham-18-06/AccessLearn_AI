"""Rule-based quiz scoring and adaptive learning recommendations."""

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import TypeAlias

QuizQuestion: TypeAlias = Mapping[str, object]
WeakTopic: TypeAlias = dict[str, str | int]
Recommendation: TypeAlias = dict[str, str | None]

SIGNIFICANT_SCORE_CHANGE: float = 10.0


def _is_sequence(value: object) -> bool:
    """Return whether a value is a sequence of quiz data, excluding text."""
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _valid_question(question: object) -> bool:
    """Check the fields needed to score one quiz question."""
    if not isinstance(question, Mapping):
        return False

    prompt = question.get("question")
    options = question.get("options")
    correct_answer = question.get("answer")

    return (
        isinstance(prompt, str)
        and bool(prompt.strip())
        and _is_sequence(options)
        and len(options) > 0
        and isinstance(correct_answer, int)
        and not isinstance(correct_answer, bool)
        and 0 <= correct_answer < len(options)
    )


def _valid_student_answer(answer: object) -> bool:
    """Return whether a student answer is an integer option index."""
    return isinstance(answer, int) and not isinstance(answer, bool)


def calculate_score(
    questions: Sequence[QuizQuestion], answers: Sequence[object]
) -> float:
    """Calculate the percentage of valid questions answered correctly.

    Invalid question records are skipped. A missing or invalid answer for a
    valid question is counted as incorrect. The result is rounded to 2 decimals.
    """
    if not _is_sequence(questions) or not _is_sequence(answers):
        return 0.0

    valid_question_count = 0
    correct_answer_count = 0

    for index, question in enumerate(questions):
        if not _valid_question(question):
            continue

        valid_question_count += 1
        if index >= len(answers) or not _valid_student_answer(answers[index]):
            continue

        if answers[index] == question["answer"]:
            correct_answer_count += 1

    if valid_question_count == 0:
        return 0.0

    return round(correct_answer_count / valid_question_count * 100, 2)


def detect_weak_topics(
    questions: Sequence[QuizQuestion], answers: Sequence[object]
) -> list[WeakTopic]:
    """Group incorrect answers by topic and assign a severity."""
    if not _is_sequence(questions) or not _is_sequence(answers):
        return []

    mistakes_by_topic: dict[str, int] = {}

    for index, question in enumerate(questions):
        if not _valid_question(question):
            continue

        answer = answers[index] if index < len(answers) else None
        if _valid_student_answer(answer) and answer == question["answer"]:
            continue

        topic_value = question.get("topic")
        topic = topic_value.strip() if isinstance(topic_value, str) else "Unknown"
        if not topic:
            topic = "Unknown"
        mistakes_by_topic[topic] = mistakes_by_topic.get(topic, 0) + 1

    return [
        {
            "topic": topic,
            "mistakes": mistakes,
            "severity": "high" if mistakes >= 2 else "medium",
        }
        for topic, mistakes in mistakes_by_topic.items()
    ]


def _most_important_topic(weak_topics: Sequence[Mapping[str, object]]) -> str | None:
    """Choose the weak topic with the most mistakes, preserving ties."""
    most_important: str | None = None
    highest_mistake_count = -1

    for weak_topic in weak_topics:
        topic = weak_topic.get("topic")
        mistakes = weak_topic.get("mistakes")
        if (
            isinstance(topic, str)
            and isinstance(mistakes, int)
            and not isinstance(mistakes, bool)
            and mistakes > highest_mistake_count
        ):
            most_important = topic
            highest_mistake_count = mistakes

    return most_important


def recommend_next_action(
    score: float,
    weak_topics: Sequence[Mapping[str, object]],
    previous_score: float | None = None,
) -> Recommendation:
    """Recommend a rule-based next action using score and weak topics.

    A score change of at least 10 percentage points favors targeted practice
    after improvement or easier revision after a drop.
    """
    if not isinstance(score, (int, float)) or isinstance(score, bool) or not isfinite(score):
        score = 0.0

    topic = _most_important_topic(weak_topics) if _is_sequence(weak_topics) else None

    previous_is_valid = (
        isinstance(previous_score, (int, float))
        and not isinstance(previous_score, bool)
        and isfinite(previous_score)
        and 0 <= previous_score <= 100
    )
    if previous_is_valid and score - previous_score >= SIGNIFICANT_SCORE_CHANGE:
        return {
            "type": "PRACTICE",
            "topic": topic,
            "difficulty": "medium",
            "reason": "The learner needs targeted practice on weak topics.",
        }

    if previous_is_valid and previous_score - score >= SIGNIFICANT_SCORE_CHANGE:
        return {
            "type": "REVISION",
            "topic": topic,
            "difficulty": "easy",
            "reason": "The learner needs to reinforce weak concepts with simpler explanations.",
        }

    if score < 50:
        action_type = "REVISION"
        difficulty = "easy"
        reason = "The learner needs to reinforce weak concepts with simpler explanations."
    elif score < 80:
        action_type = "PRACTICE"
        difficulty = "medium"
        reason = "The learner needs targeted practice on weak topics."
    else:
        action_type = "ADVANCE"
        difficulty = "hard"
        reason = "The learner is ready to progress to harder material."

    return {
        "type": action_type,
        "topic": topic,
        "difficulty": difficulty,
        "reason": reason,
    }


def evaluate_quiz(
    questions: Sequence[QuizQuestion],
    answers: Sequence[object],
    previous_score: float | None = None,
) -> dict[str, object]:
    """Score a quiz and return weak topics and a proposed next action."""
    score = calculate_score(questions, answers)
    weak_topics = detect_weak_topics(questions, answers)
    next_action = recommend_next_action(score, weak_topics, previous_score)

    return {
        "score": score,
        "weak_topics": weak_topics,
        "next_action": next_action,
        "approval_required": True,
    }


def apply_approved_action(
    recommendation: Mapping[str, object], approved: bool
) -> dict[str, object]:
    """Return an action only after learner approval."""
    if not approved:
        return {"status": "approval_required", "action": None}

    return {"status": "approved", "action": dict(recommendation)}
