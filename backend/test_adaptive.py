"""Tests for the adaptive learning logic."""

import unittest

from backend.adaptive import (
    apply_approved_action,
    detect_weak_topics,
    evaluate_quiz,
    recommend_next_action,
)


class AdaptiveLearningTests(unittest.TestCase):
    def test_score_below_50_recommends_easy_revision(self) -> None:
        action = recommend_next_action(49, [])

        self.assertEqual(action["type"], "REVISION")
        self.assertEqual(action["difficulty"], "easy")

    def test_score_between_50_and_79_recommends_medium_practice(self) -> None:
        for score in (50, 79):
            with self.subTest(score=score):
                action = recommend_next_action(score, [])

                self.assertEqual(action["type"], "PRACTICE")
                self.assertEqual(action["difficulty"], "medium")

    def test_score_of_80_or_more_recommends_hard_advance(self) -> None:
        action = recommend_next_action(80, [])

        self.assertEqual(action["type"], "ADVANCE")
        self.assertEqual(action["difficulty"], "hard")

    def test_repeated_mistakes_in_topic_have_high_severity(self) -> None:
        questions = [
            {"question": "First", "options": ["A", "B"], "answer": 0, "topic": "Arrays"},
            {"question": "Second", "options": ["A", "B"], "answer": 1, "topic": "Arrays"},
        ]

        weak_topics = detect_weak_topics(questions, [1, 0])

        self.assertEqual(
            weak_topics,
            [{"topic": "Arrays", "mistakes": 2, "severity": "high"}],
        )

    def test_significant_improvement_recommends_targeted_practice(self) -> None:
        weak_topics = [{"topic": "Arrays", "mistakes": 1, "severity": "medium"}]

        action = recommend_next_action(70, weak_topics, previous_score=60)

        self.assertEqual(action["type"], "PRACTICE")
        self.assertEqual(action["topic"], "Arrays")
        self.assertIn("targeted practice", action["reason"])

    def test_significant_drop_recommends_easy_revision(self) -> None:
        action = recommend_next_action(60, [], previous_score=70)

        self.assertEqual(action["type"], "REVISION")
        self.assertEqual(action["difficulty"], "easy")

    def test_unapproved_action_is_not_returned_for_application(self) -> None:
        recommendation = {"type": "PRACTICE", "topic": "Arrays"}

        result = apply_approved_action(recommendation, approved=False)

        self.assertEqual(result, {"status": "approval_required", "action": None})

    def test_empty_quiz_and_invalid_answers_do_not_crash(self) -> None:
        empty_result = evaluate_quiz([], [])
        invalid_result = evaluate_quiz(
            [{"question": "Pick one", "options": ["A", "B"], "answer": 1, "topic": "Arrays"}],
            [None],
        )

        self.assertEqual(empty_result["score"], 0.0)
        self.assertEqual(invalid_result["score"], 0.0)
        self.assertEqual(
            invalid_result["weak_topics"],
            [{"topic": "Arrays", "mistakes": 1, "severity": "medium"}],
        )


if __name__ == "__main__":
    unittest.main()
