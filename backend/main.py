from dataclasses import dataclass
from logging import getLogger
from secrets import token_urlsafe
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, StrictBool, field_validator
from starlette.concurrency import run_in_threadpool

from ai.learning import generate_learning_response
from backend.adaptive import apply_approved_action, evaluate_quiz
from backend.pdf_utils import extract_pdf_text, prepare_text


logger = getLogger(__name__)


app = FastAPI(
    title="AccessLearn AI",
    description=(
        "An accessible, adaptive learning copilot. Quiz sessions are stored "
        "in memory and disappear when the server restarts."
    ),
    version="1.0.0",
)


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    topic: str


class LessonResponse(BaseModel):
    lesson: str
    quiz: list[QuizQuestion]
    quiz_id: str
    source: str
    ai_status: str
    next_action: dict


class QuizSubmission(BaseModel):
    answers: list[int | None]

    @field_validator("answers", mode="before")
    @classmethod
    def validate_answers(cls, value: object) -> object:
        if not isinstance(value, list):
            raise ValueError("answers must be a list of exactly three values.")
        if len(value) != 3:
            raise ValueError("Submit exactly three answers.")
        if any(
            answer is not None
            and (type(answer) is not int or answer not in (0, 1, 2))
            for answer in value
        ):
            raise ValueError("Each answer must be 0, 1, 2, or null.")
        return value


class QuizApproval(BaseModel):
    approved: StrictBool


@dataclass
class QuizSession:
    questions: list[dict[str, object]]
    pending_recommendation: dict[str, object] | None = None


# Quiz sessions are intentionally in memory for the hackathon demo. They are
# lost whenever the server restarts.
quiz_sessions: dict[str, QuizSession] = {}


@app.get("/")
def home():
    return {
        "message": "Welcome to AccessLearn AI!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


def _generate_lesson_data(
    text: str,
    learner_level: str,
    input_type: str,
) -> tuple[dict, list[dict[str, object]]]:
    result = generate_learning_response(
        study_material=text,
        learner_level=learner_level,
        input_type=input_type,
    )

    default_topic = result["next_action"]["topic"]
    stored_quiz: list[dict[str, object]] = []
    learner_quiz: list[dict[str, object]] = []

    for item in result["quiz"]:
        topic = item.get("topic", default_topic)
        stored_quiz.append(
            {
                "question": item["question"],
                "options": item["options"],
                "topic": topic,
                "answer": item["answer"],
            }
        )
        learner_quiz.append(
            {
                "question": item["question"],
                "options": item["options"],
                "topic": topic,
            }
        )

    learner_result = {
        "lesson": result["lesson"],
        "quiz": learner_quiz,
        "next_action": result["next_action"],
        "ai_status": "gemma4",
    }
    return learner_result, stored_quiz


def generate_lesson(
    text: str,
    learner_level: str,
    input_type: str,
) -> dict:
    """Generate a lesson while omitting answer keys from the returned quiz."""
    lesson, _ = _generate_lesson_data(text, learner_level, input_type)
    return lesson


@app.post("/api/lesson", response_model=LessonResponse)
async def create_lesson(
    text: Annotated[str | None, Form()] = None,
    learner_level: Annotated[str, Form()] = "beginner",
    input_type: Annotated[str, Form()] = "text",
    file: Annotated[UploadFile | None, File()] = None,
):
    if learner_level not in {"beginner", "intermediate", "advanced"}:
        raise HTTPException(
            status_code=400,
            detail="Learner level must be beginner, intermediate, or advanced.",
        )

    if input_type not in {"text", "question"}:
        raise HTTPException(
            status_code=400,
            detail="input_type must be 'text' or 'question'.",
        )

    if file is not None:
        if input_type != "text":
            raise HTTPException(
                status_code=400,
                detail="PDF uploads must use input_type='text'.",
            )

        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="Please upload a PDF file.",
            )

        try:
            pdf_bytes = await file.read()
        finally:
            await file.close()

        try:
            study_text = extract_pdf_text(pdf_bytes)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        source = "pdf"

    elif text and text.strip():
        try:
            study_text = prepare_text(text)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        source = input_type

    else:
        raise HTTPException(
            status_code=400,
            detail="Provide study text, ask a question, or upload a PDF.",
        )

    try:
        result = await run_in_threadpool(
            _generate_lesson_data,
            study_text,
            learner_level,
            input_type,
        )

        lesson, stored_quiz = result
        quiz_id = token_urlsafe(16)
        quiz_sessions[quiz_id] = QuizSession(questions=stored_quiz)
        lesson["source"] = source
        lesson["quiz_id"] = quiz_id
        return LessonResponse(**lesson)

    except (ValueError, RuntimeError) as exc:
        logger.warning("Gemma generation failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="AI lesson generation failed. Check the AI service.",
        ) from exc
    except Exception:
        logger.exception("Unexpected lesson error")
        raise HTTPException(
            status_code=502,
            detail="Lesson generation failed. Check the server logs.",
        ) from exc


@app.post("/api/quiz/{quiz_id}/submit")
def submit_quiz(quiz_id: str, submission: QuizSubmission):
    session = quiz_sessions.get(quiz_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    evaluation = evaluate_quiz(session.questions, submission.answers)
    session.pending_recommendation = evaluation["next_action"]
    return evaluation


@app.post("/api/quiz/{quiz_id}/approve")
def approve_quiz_action(quiz_id: str, approval: QuizApproval):
    session = quiz_sessions.get(quiz_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    if session.pending_recommendation is None:
        raise HTTPException(
            status_code=409,
            detail="Submit the quiz before approving a recommendation.",
        )

    result = apply_approved_action(session.pending_recommendation, approval.approved)
    if approval.approved:
        session.pending_recommendation = None
    return result
