# AccessLearn AI

AccessLearn AI is an accessible learning copilot for visually impaired students. It turns pasted study material or uploaded PDFs into a personalized lesson, a short adaptive quiz, and a recommended next learning action.

## Features

- Generate lessons from pasted notes or PDF documents
- Choose beginner, intermediate, or advanced learning levels
- Gemma-powered learning content generation
- Adaptive quiz evaluation with score and weak-topic feedback
- Recommended revision, practice, or advancement actions
- Learner approval flow for recommended next steps
- Browser text-to-speech controls for lesson content
- Responsive, keyboard-friendly React interface
- Screen-reader announcements for loading, errors, results, and success states

## Project structure

```text
AccessLearn_AI/
├── ai/
│   └── learning.py          # Gemma integration
├── backend/
│   ├── adaptive.py          # Quiz scoring and recommendations
│   ├── main.py              # FastAPI application and API routes
│   └── pdf_utils.py         # PDF and text extraction
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main learning experience
│   │   ├── App.css          # Dashboard styling
│   │   └── main.jsx         # React entry point
│   └── package.json
└── README.md
```

## Requirements

- Python 3.10 or newer
- Node.js 18 or newer
- npm
- A configured Gemma/AI service for lesson generation

## Backend setup

From the repository root, create and activate a virtual environment, then install the backend dependencies used by the project:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn python-multipart pydantic pypdf
```

Configure any AI provider environment variables required by `ai/learning.py`, then start the API:

```powershell
uvicorn backend.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.

## Frontend setup

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

For a production build:

```powershell
cd frontend
npm run build
```

## API endpoints

### Generate a lesson

`POST /api/lesson`

Send `multipart/form-data` with:

- `text`: pasted study material
- `learner_level`: `beginner`, `intermediate`, or `advanced`
- `input_type`: `text` or `question`
- `file`: optional PDF upload

### Submit a quiz

`POST /api/quiz/{quiz_id}/submit`

```json
{
  "answers": [0, 1, 2]
}
```

### Approve or reject a recommendation

`POST /api/quiz/{quiz_id}/approve`

```json
{
  "approved": true
}
```

Quiz sessions are stored in memory for the demo and are cleared when the backend restarts.

## Accessibility

The frontend uses semantic headings, form labels, fieldsets, keyboard-visible focus indicators, readable contrast, accessible names for icon buttons, and live regions for important state changes. Lesson content can also be read aloud using the browser's Web Speech API.

## Development checks

```powershell
cd frontend
npm run lint
npm run build
```
