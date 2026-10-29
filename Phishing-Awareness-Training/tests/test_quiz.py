from datetime import date

import pytest

from quiz import (
    PASS_PERCENTAGE,
    QUESTIONS,
    build_certificate_html,
    build_report,
    evaluate_quiz,
)

CORRECT = tuple(question.options[question.answer] for question in QUESTIONS)


def _wrong_answer(question):
    return next(option for index, option in enumerate(question.options) if index != question.answer)


def test_all_correct_passes():
    result = evaluate_quiz(CORRECT)
    assert result.score == 5
    assert result.total == 5
    assert result.percentage == 100
    assert result.unanswered == 0
    assert result.passed is True


def test_eighty_percent_passes():
    answers = list(CORRECT)
    answers[0] = _wrong_answer(QUESTIONS[0])
    result = evaluate_quiz(answers)
    assert result.score == 4
    assert result.percentage == PASS_PERCENTAGE
    assert result.passed is True


def test_below_eighty_percent_fails():
    answers = list(CORRECT)
    answers[0] = _wrong_answer(QUESTIONS[0])
    answers[1] = _wrong_answer(QUESTIONS[1])
    result = evaluate_quiz(answers)
    assert result.score == 3
    assert result.percentage == 60
    assert result.passed is False


def test_unanswered_question_blocks_certificate():
    answers = (None, *CORRECT[1:])
    result = evaluate_quiz(answers)
    assert result.score == 4
    assert result.percentage == 80
    assert result.unanswered == 1
    assert result.passed is False


def test_wrong_number_of_answers_is_rejected():
    with pytest.raises(ValueError):
        evaluate_quiz(CORRECT[:4])


def test_report_contains_question_breakdown():
    result = evaluate_quiz(CORRECT)
    report = build_report(result, "Ada Lovelace", date(2026, 10, 28))
    assert "Learner: Ada Lovelace" in report
    assert "Score: 5/5 (100%)" in report
    assert "Status: PASSED" in report
    assert "Question 1: Correct" in report
    assert "Selected:" in report
    assert "Correct answer:" in report
    assert "Passing score: 80%" in report


def test_certificate_contains_learner_details():
    result = evaluate_quiz(CORRECT)
    certificate = build_certificate_html(result, "Ada Lovelace", date(2026, 10, 28))
    assert "Ada Lovelace" in certificate
    assert "5/5" in certificate
    assert "100%" in certificate
    assert "PAT-" in certificate
    assert "not independently verifiable" in certificate


def test_certificate_escapes_html_in_name():
    result = evaluate_quiz(CORRECT)
    certificate = build_certificate_html(result, "<script>alert(1)</script>", date(2026, 10, 28))
    assert "<script>" not in certificate
    assert "&lt;script&gt;" in certificate


def test_certificate_requires_a_pass():
    result = evaluate_quiz((None, *CORRECT[1:]))
    with pytest.raises(ValueError):
        build_certificate_html(result, "Ada Lovelace")
