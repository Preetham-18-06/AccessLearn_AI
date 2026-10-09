
import json
import ollama

MODEL = "gemma4:31b-cloud"


def generate_learning_response(study_material: str, learner_level: str = "beginner") -> dict:
    if not study_material or not study_material.strip():
        raise ValueError("Study material cannot be empty")

    prompt = f"""
You are AccessLearn AI, a learning assistant for visually impaired students.
Explain concepts simply and clearly.

Learner level: {learner_level}

Study material:
{study_material}

Generate:
1. A lesson with exactly 3 simple bullet points.
2. Exactly 3 multiple-choice questions.
3. Exactly 3 options for each question.
4. The correct answer as an index: 0, 1, or 2.
5. A generic next action.

Return only valid JSON in this format:
{{
  "lesson": "- First point\\n- Second point\\n- Third point",
  "quiz": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C"],
      "answer": 0
    }}
  ],
  "next_action": {{
    "type": "practice",
    "topic": "Main topic",
    "reason": "Complete the quiz to identify topics for revision."
  }}
}}
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Return only valid JSON without Markdown fences."
            },
            {"role": "user", "content": prompt}
        ],
        format="json"
    )

    result = json.loads(response["message"]["content"])

    if not isinstance(result, dict):
        raise ValueError("AI response must be a JSON object")

    if not isinstance(result.get("lesson"), str):
        raise ValueError("Invalid lesson")

    quiz = result.get("quiz")

    if not isinstance(quiz, list) or len(quiz) != 3:
        raise ValueError("Expected exactly 3 quiz questions")

    for question in quiz:
        if not isinstance(question, dict):
            raise ValueError("Invalid quiz question")

        if not isinstance(question.get("question"), str):
            raise ValueError("Missing question text")

        options = question.get("options")
        answer = question.get("answer")

        if not isinstance(options, list) or len(options) != 3:
            raise ValueError("Each question needs exactly 3 options")

        if (
            not isinstance(answer, int)
            or isinstance(answer, bool)
            or answer not in range(3)
        ):
            raise ValueError("Answer must be 0, 1, or 2")

    if not isinstance(result.get("next_action"), dict):
        raise ValueError("Missing next_action")

    return result


if __name__ == "__main__":
    sample = """
    Photosynthesis is how plants make food.
    Plants use sunlight, water, and carbon dioxide to produce glucose.
    Oxygen is released during this process.
    """

    try:
        output = generate_learning_response(sample, "beginner")
        print(json.dumps(output, indent=2, ensure_ascii=False))
    except Exception as error:
        print(f"AI request failed: {error}")

