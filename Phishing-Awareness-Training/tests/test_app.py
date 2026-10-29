from pathlib import Path

from streamlit.testing.v1 import AppTest

from quiz import QUESTIONS

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
CORRECT = tuple(question.options[question.answer] for question in QUESTIONS)


def _new_app():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not app.exception, [str(error.value) for error in app.exception]
    return app


def _button(app, label):
    return next(button for button in app.button if button.label == label)


def _submit(app, answers, name="Test Learner"):
    app.text_input[0].set_value(name)
    for index, answer in enumerate(answers):
        app.radio[index].set_value(answer)
    _button(app, "Submit quiz").click().run()


def _wrong_answer(question):
    return next(option for index, option in enumerate(question.options) if index != question.answer)


def test_app_loads_with_five_tabs_and_quiz():
    app = _new_app()
    assert len(app.tabs) == 5
    assert len(app.radio) == 5
    assert [button.label for button in app.button] == ["Submit quiz"]


def test_unanswered_quiz_is_blocked():
    app = _new_app()
    _button(app, "Submit quiz").click().run()
    assert any("answer all questions" in warning.value.lower() for warning in app.warning)
    assert not any("Your score" in subheader.value for subheader in app.subheader)


def test_full_score_shows_success_and_downloads():
    app = _new_app()
    _submit(app, CORRECT)
    assert not app.exception
    assert any("Your score: 5/5" in subheader.value for subheader in app.subheader)
    assert any("Training completed successfully" in success.value for success in app.success)
    downloads = [button.label for button in app.get("download_button")]
    assert "Download Completion Certificate" in downloads
    assert "Download Quiz Report" in downloads


def test_result_hides_form_and_shows_selected_answer():
    app = _new_app()
    answers = list(CORRECT)
    answers[0] = _wrong_answer(QUESTIONS[0])
    _submit(app, answers)
    assert not app.radio
    captions = " ".join(caption.value for caption in app.caption)
    assert f"Your answer: {answers[0]}" in captions
    assert f"Correct answer: {QUESTIONS[0].options[QUESTIONS[0].answer]}" in captions


def test_result_survives_plain_rerun():
    app = _new_app()
    _submit(app, CORRECT)
    app.run()
    assert any("Your score: 5/5" in subheader.value for subheader in app.subheader)
    assert len(app.get("download_button")) == 2


def test_below_threshold_gets_report_but_no_certificate():
    app = _new_app()
    answers = list(CORRECT)
    answers[0] = _wrong_answer(QUESTIONS[0])
    answers[1] = _wrong_answer(QUESTIONS[1])
    _submit(app, answers)
    assert any("Your score: 3/5" in subheader.value for subheader in app.subheader)
    assert any("Score at least 80%" in info.value for info in app.info)
    downloads = [button.label for button in app.get("download_button")]
    assert "Download Quiz Report" in downloads
    assert "Download Completion Certificate" not in downloads


def test_retry_clears_result_and_resets_questions():
    app = _new_app()
    _submit(app, CORRECT)
    _button(app, "Retry quiz").click().run()
    assert not any("Your score" in subheader.value for subheader in app.subheader)
    assert not app.get("download_button")
    assert [radio.value for radio in app.radio] == [None] * len(QUESTIONS)
