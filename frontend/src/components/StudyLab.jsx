import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  BookOpen, 
  Layers, 
  RotateCw, 
  CheckCircle2, 
  ChevronRight, 
  ChevronLeft,
  X,
  Award,
  Sparkles,
  ArrowRight,
  Info
} from 'lucide-react'

export default function StudyLab({ uploadId, userId, onBack }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('summary')
  const [flashcardIdx, setFlashcardIdx] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [quizIdx, setQuizIdx] = useState(0)
  const [quizScore, setQuizScore] = useState(0)
  const [showQuizResult, setShowQuizResult] = useState(false)
  const [quizAnswers, setQuizAnswers] = useState([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(`/api/v1/uploads/${uploadId}`)
        setData(response.data)
      } catch (err) {
        console.error("Failed to fetch artifact", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [uploadId])

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-2 border-white/10 border-t-white/80 rounded-full animate-spin" />
        <p className="text-white/40 text-sm font-medium tracking-widest uppercase">Opening Artifact</p>
      </div>
    )
  }

  if (!data?.study_package?.data) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8">
        <Info size={48} className="text-white/20 mb-4" />
        <h3 className="text-xl font-medium mb-2">Package Incomplete</h3>
        <p className="text-white/40 max-w-xs mb-6">This artifact does not have a valid study package. It might still be processing.</p>
        <button onClick={onBack} className="liquid-glass px-6 py-2 rounded-xl text-sm transition-all hover:bg-white/5">Back to Academy</button>
      </div>
    )
  }

  const packageData = data.study_package.data
  const tabs = [
    { id: 'summary', label: 'Summary', icon: BookOpen },
    { id: 'concepts', label: 'Concepts', icon: Layers },
    { id: 'flashcards', label: 'Flashcards', icon: RotateCw },
    { id: 'quiz', label: 'Quiz', icon: Award },
  ]

  const handleQuizAnswer = (isCorrect) => {
    const newAnswers = [...quizAnswers, isCorrect]
    setQuizAnswers(newAnswers)
    if (isCorrect) setQuizScore(quizScore + 1)
    
    if (quizIdx < packageData.questions.length - 1) {
      setQuizIdx(quizIdx + 1)
    } else {
      setShowQuizResult(true)
      // Save performance to DB
      const scorePercentage = ((quizScore + (isCorrect ? 1 : 0)) / packageData.questions.length) * 100
      axios.post('/api/v1/performance', new URLSearchParams({
        upload_id: uploadId,
        user_id: userId,
        score: scorePercentage,
        notes: `Completed quiz for ${data.file_name}`
      }))
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* HEADER */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="p-2 hover:bg-white/5 rounded-full transition-colors text-white/40 hover:text-white">
            <ChevronLeft size={24} />
          </button>
          <div>
            <h2 className="text-2xl font-medium tracking-tighter truncate max-w-[300px]">
              {data.topic || data.file_name}
            </h2>
            <p className="text-white/20 text-xs tracking-widest uppercase font-bold">{data.subject || 'Knowledge Artifact'}</p>
          </div>
        </div>

        <div className="flex p-1 bg-white/5 rounded-2xl liquid-glass">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-medium transition-all duration-300
                ${activeTab === tab.id ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white/60'}
              `}
            >
              <tab.icon size={14} />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* CONTENT AREA */}
      <div className="flex-1 min-h-0 bg-white/[0.02] rounded-[2.5rem] border border-white/5 p-10 overflow-auto custom-scrollbar">
        <AnimatePresence mode="wait">
          {/* SUMMARY TAB */}
          {activeTab === 'summary' && (
            <motion.div
              key="summary"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="max-w-3xl mx-auto space-y-8"
            >
              <h3 className="text-4xl font-medium tracking-tighter">
                {packageData.summary?.title}
              </h3>
              <div className="prose prose-invert max-w-none text-white/70 leading-relaxed text-lg space-y-6">
                {packageData.summary?.content.split('\n\n').map((para, i) => (
                  <p key={i}>{para}</p>
                ))}
              </div>
            </motion.div>
          )}

          {/* CONCEPTS TAB */}
          {activeTab === 'concepts' && (
            <motion.div
              key="concepts"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-6"
            >
              {packageData.concepts?.map((concept, i) => (
                <div key={i} className="liquid-glass p-8 rounded-3xl border border-white/5 hover:border-white/10 transition-colors">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-xl font-semibold tracking-tight">{concept.name}</h4>
                    <span className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase ${
                      concept.importance === 'high' ? 'bg-white/20 text-white' : 'bg-white/5 text-white/40'
                    }`}>
                      {concept.importance}
                    </span>
                  </div>
                  <p className="text-white/50 leading-relaxed text-sm">{concept.definition}</p>
                </div>
              ))}
            </motion.div>
          )}

          {/* FLASHCARDS TAB */}
          {activeTab === 'flashcards' && (
            <motion.div
              key="flashcards"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
              className="h-full flex flex-col items-center justify-center space-y-12"
            >
              <div 
                className="perspective-1000 w-full max-w-xl h-80 cursor-pointer"
                onClick={() => setIsFlipped(!isFlipped)}
              >
                <div className={`relative w-full h-full transition-transform duration-700 preserve-3d ${isFlipped ? 'rotate-y-180' : ''}`}>
                  {/* FRONT */}
                  <div className="absolute inset-0 backface-hidden liquid-glass-strong rounded-[3rem] p-10 flex flex-col items-center justify-center text-center shadow-2xl">
                    <span className="text-[10px] font-bold tracking-widest uppercase text-white/30 mb-6">Question {flashcardIdx + 1}</span>
                    <p className="text-2xl font-medium tracking-tight leading-relaxed">
                      {packageData.flashcards[flashcardIdx]?.question}
                    </p>
                    <div className="mt-8 flex items-center gap-2 text-white/20 text-xs font-bold uppercase tracking-widest">
                      <RotateCw size={12} /> Click to reveal
                    </div>
                  </div>
                  {/* BACK */}
                  <div className="absolute inset-0 backface-hidden rotate-y-180 bg-white text-black rounded-[3rem] p-10 flex flex-col items-center justify-center text-center shadow-2xl">
                  <span className="text-[10px] font-bold tracking-widest uppercase text-black/30 mb-6 font-poppins">Discovery</span>
                    <p className="text-xl font-semibold leading-relaxed font-poppins">
                      {packageData.flashcards[flashcardIdx]?.answer}
                    </p>
                    <div className="mt-8 px-4 py-1.5 rounded-full border border-black/10 text-[10px] font-bold uppercase tracking-widest opacity-60">
                      Concept Verified
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-8">
                <button 
                  onClick={(e) => { e.stopPropagation(); setFlashcardIdx(Math.max(0, flashcardIdx - 1)); setIsFlipped(false); }}
                  disabled={flashcardIdx === 0}
                  className="p-4 rounded-full liquid-glass text-white/40 hover:text-white disabled:opacity-20 transition-all"
                >
                  <ChevronLeft size={24} />
                </button>
                <span className="text-sm font-bold tracking-widest text-white/40">
                  {flashcardIdx + 1} / {packageData.flashcards.length}
                </span>
                <button 
                  onClick={(e) => { e.stopPropagation(); setFlashcardIdx(Math.min(packageData.flashcards.length - 1, flashcardIdx + 1)); setIsFlipped(false); }}
                  disabled={flashcardIdx === packageData.flashcards.length - 1}
                  className="p-4 rounded-full liquid-glass text-white/40 hover:text-white disabled:opacity-20 transition-all"
                >
                  <ChevronRight size={24} />
                </button>
              </div>
            </motion.div>
          )}

          {/* QUIZ TAB */}
          {activeTab === 'quiz' && (
            <motion.div
              key="quiz"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full max-w-2xl mx-auto flex flex-col"
            >
              {!showQuizResult ? (
                <div className="flex-1 flex flex-col justify-center">
                  <div className="mb-12">
                    <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-bold tracking-widest uppercase text-white/30">Verification {quizIdx + 1} / {packageData.questions.length}</span>
                    <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[8px] font-bold tracking-widest uppercase text-white/40">
                        {packageData.questions[quizIdx]?.question_type}
                    </span>
                    </div>
                    <h3 className="text-3xl font-medium tracking-tighter">
                      {packageData.questions[quizIdx]?.question}
                    </h3>
                  </div>

                  <div className="space-y-4">
                    <p className="text-white/30 text-xs italic mb-8">Take a moment to formulate your answer, then verify below.</p>
                    
                    <button 
                      onClick={() => handleQuizAnswer(true)}
                      className="w-full group relative p-6 rounded-3xl bg-white/5 border border-white/5 hover:bg-white text-left transition-all duration-500 overflow-hidden"
                    >
                      <div className="relative z-10 flex items-center justify-between group-hover:text-black transition-colors">
                        <span className="text-lg font-medium tracking-tight">I knew this answer</span>
                        <CheckCircle2 size={24} className="text-white/20 group-hover:text-black/40" />
                      </div>
                      <div className="absolute top-0 right-0 w-24 h-24 bg-white/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>

                    <button 
                      onClick={() => handleQuizAnswer(false)}
                      className="w-full group p-6 rounded-3xl bg-white/5 border border-white/5 hover:border-white/10 text-left transition-all"
                    >
                      <div className="flex items-center justify-between text-white/40 group-hover:text-white transition-colors">
                        <span className="text-lg font-medium tracking-tight">I need to review this</span>
                        <X size={24} className="opacity-40" />
                      </div>
                    </button>
                    
                    <div className="mt-8 p-6 bg-white/[0.02] border border-white/5 rounded-2xl">
                        <h5 className="text-[10px] font-bold tracking-widest uppercase text-white/20 mb-3 flex items-center gap-2">
                            <Sparkles size={12} /> Model Answer Preview
                        </h5>
                        <p className="text-sm text-white/50 leading-relaxed italic">
                            "{packageData.questions[quizIdx]?.model_answer.slice(0, 100)}..."
                        </p>
                    </div>
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
                    <h3 className="text-5xl font-medium tracking-tighter mb-2">Quiz Complete</h3>
                    <p className="text-white/40 text-xl font-serif italic">Your retention has been synchronized.</p>
                  </div>
                  
                  <div className="text-7xl font-bold tracking-tighter">
                    {Math.round((quizScore / packageData.questions.length) * 100)}%
                  </div>

                  <button 
                    onClick={onBack}
                    className="bg-white text-black px-10 py-4 rounded-[2rem] font-bold text-lg hover:bg-white/90 active:scale-95 transition-all flex items-center gap-3"
                  >
                    Back to Academy
                    <ArrowRight size={20} />
                  </button>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <style jsx>{`
        .perspective-1000 { perspective: 1000px; }
        .preserve-3d { transform-style: preserve-3d; }
        .backface-hidden { backface-visibility: hidden; }
        .rotate-y-180 { transform: rotateY(180deg); }
      `}</style>
    </div>
  )
}
