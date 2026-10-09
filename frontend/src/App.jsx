import { useEffect, useRef, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  const [studyText, setStudyText] = useState('')
  const [learnerLevel, setLearnerLevel] = useState('beginner')
  const [file, setFile] = useState(null)
  const [lessonData, setLessonData] = useState(null)
  const [answers, setAnswers] = useState([])
  const [quizResult, setQuizResult] = useState(null)
  const [approvalResult, setApprovalResult] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isApproving, setIsApproving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [isListening, setIsListening] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    return () => window.speechSynthesis?.cancel()
  }, [])

  const getErrorMessage = async (response) => {
    try {
      const body = await response.json()
      return body.detail || 'Something went wrong. Please try again.'
    } catch {
      return 'Something went wrong. Please try again.'
    }
  }

  const generateLesson = async (event) => {
    event.preventDefault()
    if (!studyText.trim() && !file) {
      setError('Add study material or upload a PDF before generating a lesson.')
      return
    }

    setError('')
    setNotice('')
    setIsGenerating(true)
    const formData = new FormData()
    formData.append('text', studyText)
    formData.append('learner_level', learnerLevel)
    formData.append('input_type', 'text')
    if (file) formData.append('file', file)

    try {
      const response = await fetch(`${API_URL}/api/lesson`, {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) throw new Error(await getErrorMessage(response))
      const data = await response.json()
      setLessonData(data)
      setAnswers(Array(data.quiz.length).fill(null))
      setQuizResult(null)
      setApprovalResult(null)
      setNotice('Your lesson is ready. Work through the quiz when you are ready.')
      window.setTimeout(() => document.getElementById('lesson')?.focus(), 0)
    } catch (requestError) {
      setError(requestError.message || 'Unable to generate your lesson.')
    } finally {
      setIsGenerating(false)
    }
  }

  const submitQuiz = async (event) => {
    event.preventDefault()
    if (answers.some((answer) => answer === null)) {
      setError('Please answer every question before submitting.')
      return
    }
    setError('')
    setNotice('')
    setIsSubmitting(true)
    try {
      const response = await fetch(`${API_URL}/api/quiz/${lessonData.quiz_id}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers }),
      })
      if (!response.ok) throw new Error(await getErrorMessage(response))
      const data = await response.json()
      setQuizResult(data)
      setNotice('Quiz submitted successfully. Your learning path has been updated.')
      window.setTimeout(() => document.getElementById('results')?.focus(), 0)
    } catch (requestError) {
      setError(requestError.message || 'Unable to submit your quiz.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const approveRecommendation = async (approved) => {
    setError('')
    setIsApproving(true)
    try {
      const response = await fetch(`${API_URL}/api/quiz/${lessonData.quiz_id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved }),
      })
      if (!response.ok) throw new Error(await getErrorMessage(response))
      const data = await response.json()
      setApprovalResult(data)
      setNotice(approved ? 'Recommendation approved.' : 'Recommendation declined. You can choose a different path later.')
    } catch (requestError) {
      setError(requestError.message || 'Unable to save your choice.')
    } finally {
      setIsApproving(false)
    }
  }

  const toggleSpeech = () => {
    if (!lessonData?.lesson || !window.speechSynthesis) {
      setError('Text-to-speech is not supported in this browser.')
      return
    }
    if (isListening) {
      window.speechSynthesis.cancel()
      setIsListening(false)
      return
    }
    const utterance = new SpeechSynthesisUtterance(lessonData.lesson)
    utterance.onend = () => setIsListening(false)
    utterance.onerror = () => {
      setIsListening(false)
      setError('We could not play the lesson audio. Please try again.')
    }
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)
    setIsListening(true)
  }

  const resetLesson = () => {
    window.speechSynthesis?.cancel()
    setStudyText('')
    setFile(null)
    setLessonData(null)
    setAnswers([])
    setQuizResult(null)
    setApprovalResult(null)
    setError('')
    setNotice('')
    setIsListening(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="AccessLearn AI home">
          <span className="brand-mark" aria-hidden="true">✦</span>
          <span>AccessLearn <strong>AI</strong></span>
        </a>
        <span className="header-pill"><span className="status-dot" aria-hidden="true" /> Learning copilot</span>
      </header>

      <main id="top" className="main-content">
        <section className="hero-section" aria-labelledby="welcome-heading">
          <div>
            <p className="eyebrow">PERSONALIZED LEARNING, MADE ACCESSIBLE</p>
            <h1 id="welcome-heading">Learn at your pace.<br /><span>Understand with confidence.</span></h1>
            <p className="hero-copy">Turn your study material into a clear, accessible lesson and an adaptive quiz designed around your learning needs.</p>
          </div>
          <div className="hero-orbit" aria-hidden="true">
            <div className="orbit-card orbit-card-one">Aa</div>
            <div className="orbit-card orbit-card-two">◉</div>
            <div className="hero-icon">✦</div>
          </div>
        </section>

        <div className="sr-status" role="status" aria-live="polite">{notice}</div>
        {error && <div className="alert error-alert" role="alert"><span aria-hidden="true">!</span>{error}</div>}

        {!lessonData && (
          <section className="card setup-card" aria-labelledby="setup-heading">
            <div className="section-heading">
              <div className="step-number">01</div>
              <div><p className="eyebrow">START HERE</p><h2 id="setup-heading">Add your study material</h2></div>
            </div>
            <form onSubmit={generateLesson}>
              <label className="field-label" htmlFor="study-material">Paste notes, a chapter, or a question</label>
              <textarea id="study-material" value={studyText} onChange={(event) => setStudyText(event.target.value)} placeholder="Paste the material you want to understand..." rows="7" />
              <div className="input-divider"><span>or</span></div>
              <input ref={fileInputRef} id="pdf-upload" type="file" accept="application/pdf,.pdf" onChange={(event) => setFile(event.target.files?.[0] || null)} hidden />
              {!file ? (
                <label className="upload-zone" htmlFor="pdf-upload">
                  <span className="upload-icon" aria-hidden="true">↑</span>
                  <span><strong>Upload a PDF</strong><small>Drop a file here or browse · PDF up to 10 MB</small></span>
                </label>
              ) : (
                <div className="file-chip"><span className="file-icon" aria-hidden="true">PDF</span><span className="file-name">{file.name}</span><span className="file-size">{Math.max(1, Math.round(file.size / 1024))} KB</span><button type="button" className="icon-button" onClick={() => { setFile(null); fileInputRef.current.value = '' }} aria-label={`Remove ${file.name}`}>×</button></div>
              )}
              <div className="form-footer">
                <div className="level-control"><label htmlFor="learner-level">I am learning at a</label><select id="learner-level" value={learnerLevel} onChange={(event) => setLearnerLevel(event.target.value)}><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select><span>level</span></div>
                <button className="primary-button" type="submit" disabled={isGenerating}><span>{isGenerating ? 'Building your lesson...' : 'Generate my lesson'}</span><span aria-hidden="true">{isGenerating ? '◌' : '→'}</span></button>
              </div>
            </form>
          </section>
        )}

        {lessonData && (
          <div className="lesson-flow">
            <section id="lesson" className="card lesson-card" tabIndex="-1" aria-labelledby="lesson-heading">
              <div className="section-heading lesson-heading"><div className="step-number">02</div><div><p className="eyebrow">YOUR PERSONALIZED LESSON</p><h2 id="lesson-heading">Let&apos;s make this clear</h2></div><span className="source-badge">{lessonData.source === 'pdf' ? 'From your PDF' : 'From your notes'}</span></div>
              <div className="lesson-text">{lessonData.lesson.split('\n').map((paragraph, index) => paragraph.trim() && <p key={index}>{paragraph}</p>)}</div>
              <div className="lesson-actions"><button type="button" className="secondary-button" onClick={toggleSpeech} aria-pressed={isListening}><span aria-hidden="true">{isListening ? '■' : '▶'}</span>{isListening ? 'Stop listening' : 'Listen to lesson'}</button><span className="accessible-note">You can listen to this lesson with text-to-speech.</span></div>
            </section>

            <section className="card quiz-card" aria-labelledby="quiz-heading">
              <div className="section-heading"><div className="step-number">03</div><div><p className="eyebrow">CHECK YOUR UNDERSTANDING</p><h2 id="quiz-heading">A quick knowledge check</h2></div></div>
              <form onSubmit={submitQuiz}>
                <div className="quiz-list">{lessonData.quiz.map((question, questionIndex) => <fieldset className="question" key={`${question.question}-${questionIndex}`}><legend><span className="question-number">{String(questionIndex + 1).padStart(2, '0')}</span>{question.question}</legend><div className="options">{question.options.map((option, optionIndex) => <label className={`option ${answers[questionIndex] === optionIndex ? 'selected' : ''}`} key={option}><input type="radio" name={`question-${questionIndex}`} value={optionIndex} checked={answers[questionIndex] === optionIndex} onChange={() => setAnswers((current) => current.map((answer, index) => index === questionIndex ? optionIndex : answer))} /><span className="radio-marker" aria-hidden="true">{answers[questionIndex] === optionIndex ? '✓' : ''}</span>{option}</label>)}</div></fieldset>)}</div>
                <div className="quiz-footer"><span>{answers.filter((answer) => answer !== null).length} of {lessonData.quiz.length} answered</span><button className="primary-button" type="submit" disabled={isSubmitting}><span>{isSubmitting ? 'Checking...' : 'Submit answers'}</span><span aria-hidden="true">→</span></button></div>
              </form>
            </section>

            {quizResult && <section id="results" className="results-area" tabIndex="-1" aria-labelledby="results-heading">
              <div className="score-card card"><div className="score-circle"><strong>{Math.round(quizResult.score)}</strong><span>%</span></div><div><p className="eyebrow">YOUR RESULT</p><h2 id="results-heading">{quizResult.score >= 80 ? 'Excellent work!' : quizResult.score >= 50 ? 'Good progress!' : 'Let&apos;s keep building.'}</h2><p>You&apos;re making progress. Use the recommendation below to keep going.</p></div></div>
              <div className="card recommendation-card"><div className="recommendation-icon" aria-hidden="true">✦</div><div className="recommendation-content"><p className="eyebrow">RECOMMENDED NEXT STEP</p><h2>{quizResult.next_action.type} <span className="action-topic">{quizResult.next_action.topic ? `· ${quizResult.next_action.topic}` : ''}</span></h2><p>{quizResult.next_action.reason}</p>{quizResult.weak_topics?.length > 0 && <div className="weak-topics"><strong>Topics to revisit</strong>{quizResult.weak_topics.map((item) => <span key={item.topic}>{item.topic}</span>)}</div>} {!approvalResult ? <div className="approval-actions"><button type="button" className="primary-button" onClick={() => approveRecommendation(true)} disabled={isApproving}>Approve recommendation</button><button type="button" className="text-button" onClick={() => approveRecommendation(false)} disabled={isApproving}>Not right now</button></div> : <div className={`confirmation ${approvalResult.status === 'approved' ? 'confirmed' : ''}`} role="status"><span aria-hidden="true">{approvalResult.status === 'approved' ? '✓' : '○'}</span>{approvalResult.status === 'approved' ? 'Recommendation approved — we’ll use this for your next session.' : 'Recommendation declined. You remain in control of your learning path.'}</div>}</div></div>
            </section>}
            <button type="button" className="new-lesson-button" onClick={resetLesson}>↺ <span>Start a new lesson</span></button>
          </div>
        )}
      </main>
      <footer className="footer"><span>AccessLearn AI</span><span>Built for learning without limits.</span></footer>
    </div>
  )
}

export default App
