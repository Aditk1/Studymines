/**
 * Assessment-taking view for rendering questions and submitting responses.
 */
import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ChevronRight, 
  ChevronLeft,
  X,
  Award,
  Sparkles,
  ArrowRight,
  Clock,
  CheckCircle2
} from 'lucide-react'

import { useParams, useNavigate } from 'react-router-dom'

/**
 * Assessment-taking view for rendering questions and submitting responses.
 */
export default function AssessmentView({ assessmentId: propAssessmentId, userId, onBack: propOnBack }) {
  const { id } = useParams()
  const navigate = useNavigate()
  const assessmentId = propAssessmentId || id
  const onBack = propOnBack || (() => navigate('/dashboard'))
  
  const [assessment, setAssessment] = useState(null)
  const [loading, setLoading] = useState(true)
  const [currentIdx, setCurrentIdx] = useState(0)
  const [answers, setAnswers] = useState({})
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const res = await axios.get(`/api/v1/lms/assessments/${assessmentId}`)
        setAssessment(res.data)
      } catch (err) {
        console.error("Failed to fetch assessment details", err)
      } finally {
        setLoading(false)
      }
    }
    fetchDetails()
  }, [assessmentId])

  const handleAnswer = (option) => {
    setAnswers({ ...answers, [currentIdx]: option })
  }

  const handleSubmit = async () => {
    try {
        // Calculate score client-side for immediate feedback, but backend also validates
        let correctCount = 0
        assessment.questions.forEach((q, idx) => {
            if (answers[idx] === q.content.answer) {
                correctCount++
            }
        })
        const score = (correctCount / assessment.questions.length) * 100

        const res = await axios.post(`/api/v1/lms/assessments/${assessmentId}/submit`, {
            responses: { ...answers, score: score },
            time_spent: 0 // Mocked
        }, {
           headers: { Authorization: `Bearer ${localStorage.getItem('studymines_token')}` }
        })
        setResult({ score, attempt_id: res.data.attempt_id })
        setSubmitted(true)
    } catch (err) {
        console.error("Submission failed", err)
        alert("Failed to submit assessment. Please try again.")
    }
  }

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-2 border-white/10 border-t-white/80 rounded-full animate-spin" />
        <p className="text-white/40 text-sm font-medium tracking-widest uppercase">Initializing Assessment</p>
      </div>
    )
  }

  if (!assessment || !assessment.questions || assessment.questions.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8">
        <X size={48} className="text-white/20 mb-4" />
        <h3 className="text-xl font-medium mb-2">No Questions Found</h3>
        <p className="text-white/40 max-w-xs mb-6">This assessment exists but has no questions architected yet.</p>
        <button onClick={onBack} className="liquid-glass px-6 py-2 rounded-xl text-sm transition-all hover:bg-white/5">Back to Archive</button>
      </div>
    )
  }

  const question = assessment.questions[currentIdx]

  return (
    <div className="h-full flex flex-col">
      {/* HEADER */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="p-2 hover:bg-white/5 rounded-full transition-colors text-white/40 hover:text-white">
            <ChevronLeft size={24} />
          </button>
          <div>
            <h2 className="text-2xl font-medium tracking-tighter">{assessment.title}</h2>
            <p className="text-white/20 text-xs tracking-widest uppercase font-bold">Formal Assessment • Question {currentIdx + 1} of {assessment.questions.length}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/5 rounded-full text-xs font-medium text-white/40">
                <Clock size={14} />
                {assessment.time_limit ? `${assessment.time_limit}m remaining` : 'No Limit'}
            </div>
        </div>
      </div>

      {/* CONTENT */}
      <div className="flex-1 min-h-0 bg-white/[0.02] rounded-[2.5rem] border border-white/5 p-10 overflow-auto custom-scrollbar flex flex-col">
        {!submitted ? (
            <div className="max-w-2xl mx-auto w-full flex-1 flex flex-col justify-center">
                <div className="mb-12">
                    <span className="text-[10px] font-bold tracking-[0.4em] uppercase text-white/20 mb-3 block">Contextual Inquiry</span>
                    <h3 className="text-3xl font-medium tracking-tighter leading-tight">
                        {question.content.question}
                    </h3>
                </div>

                <div className="space-y-4">
                    {question.content.options.map((opt, i) => (
                        <button 
                            key={i}
                            onClick={() => handleAnswer(opt)}
                            className={`w-full group relative p-5 rounded-2xl border transition-all duration-300 overflow-hidden text-left ${
                                answers[currentIdx] === opt 
                                ? 'bg-white text-black border-white shadow-[0_0_30px_rgba(255,255,255,0.1)]' 
                                : 'bg-white/5 border-white/5 hover:bg-white/10'
                            }`}
                        >
                            <div className="flex items-center gap-4 relative z-10">
                                <div className={`w-8 h-8 rounded-full border flex items-center justify-center text-[10px] font-bold ${
                                    answers[currentIdx] === opt ? 'bg-black/10 border-black/20' : 'border-white/10'
                                }`}>
                                    {String.fromCharCode(65 + i)}
                                </div>
                                <span className="text-lg font-medium">{opt}</span>
                                {answers[currentIdx] === opt && <CheckCircle2 size={18} className="ml-auto" />}
                            </div>
                        </button>
                    ))}
                </div>

                <div className="mt-12 flex items-center justify-between">
                    <button 
                        disabled={currentIdx === 0}
                        onClick={() => setCurrentIdx(currentIdx - 1)}
                        className="flex items-center gap-2 text-white/40 hover:text-white transition-colors disabled:opacity-0"
                    >
                        <ChevronLeft size={20} />
                        Previous
                    </button>
                    
                    {currentIdx < assessment.questions.length - 1 ? (
                        <button 
                            disabled={!answers[currentIdx]}
                            onClick={() => setCurrentIdx(currentIdx + 1)}
                            className="bg-white text-black px-8 py-3 rounded-2xl font-bold text-sm hover:bg-white/90 disabled:opacity-50 transition-all flex items-center gap-2"
                        >
                            Next Question
                            <ChevronRight size={18} />
                        </button>
                    ) : (
                        <button 
                            disabled={Object.keys(answers).length < assessment.questions.length}
                            onClick={handleSubmit}
                            className="bg-indigo-500 text-white px-10 py-3 rounded-2xl font-bold text-sm hover:bg-indigo-400 disabled:opacity-50 transition-all flex items-center gap-2 shadow-[0_0_30px_rgba(99,102,241,0.3)]"
                        >
                            Complete Assessment
                            <Sparkles size={18} />
                        </button>
                    )}
                </div>
            </div>
        ) : (
            <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex-1 flex flex-col items-center justify-center text-center space-y-8"
            >
                <div className="w-24 h-24 bg-white text-black rounded-full flex items-center justify-center shadow-[0_0_50px_rgba(255,255,255,0.2)]">
                    <Award size={48} />
                </div>
                <div>
                    <h3 className="text-5xl font-medium tracking-tighter mb-2">Architectural Victory</h3>
                    <p className="text-white/40 text-xl font-serif italic">Your cognitive mastery has been recorded in the ecosystem.</p>
                </div>
                
                <div className="text-8xl font-bold tracking-tighter">
                    {Math.round(result.score)}%
                </div>

                <div className="flex gap-4">
                    <button 
                        onClick={onBack}
                        className="bg-white/5 hover:bg-white/10 px-8 py-4 rounded-2xl font-bold text-sm transition-all"
                    >
                        View Results Breakdown
                    </button>
                    <button 
                        onClick={onBack}
                        className="bg-white text-black px-10 py-4 rounded-2xl font-bold text-sm hover:bg-white/90 active:scale-95 transition-all flex items-center gap-3"
                    >
                        Back to Archive
                        <ArrowRight size={20} />
                    </button>
                </div>
            </motion.div>
        )}
      </div>
    </div>
  )
}
