from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from backend.pdf_utils import extract_pdf_text, prepare_text
from ai.learning import generate_learning_response


app = FastAPI(
    title="AccessLearn AI",
    description="An accessible, adaptive learning copilot",
    version="1.0.0",
)


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    topic: str


class LessonResponse(BaseModel):
    lesson: str
    quiz: list[QuizQuestion]
    source: str
    ai_status: str
    next_action: dict


@app.get("/")
def home():
    return {
        "message": "Welcome to AccessLearn AI!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


def generate_lesson(
    text: str,
    learner_level: str,
    input_type: str,
) -> dict:
    result = generate_learning_response(
        study_material=text,
        learner_level=learner_level,
        input_type=input_type,
    )

    # Keep correct answer indices out of the learner-facing response.
    default_topic = result["next_action"]["topic"]

    quiz = [
        {
            "question": item["question"],
            "options": item["options"],
            "topic": item.get("topic", default_topic),
        }
        for item in result["quiz"]
    ]

    return {
        "lesson": result["lesson"],
        "quiz": quiz,
        "next_action": result["next_action"],
        "ai_status": "gemma4",
    }


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
            generate_lesson,
            study_text,
            learner_level,
            input_type,
        )

        result["source"] = source
        return LessonResponse(**result)

    except (ValueError, RuntimeError) as exc:
        print(f"Gemma generation failed: {exc}")
        raise HTTPException(
            status_code=502,
            detail="AI lesson generation failed. Check the AI service.",
        ) from exc
    except Exception as exc:
        print(f"Unexpected lesson error: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Lesson generation failed. Check the server logs.",
        ) from exc
