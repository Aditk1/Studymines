import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, Plus, CheckCircle, Clock, Sparkles, ChevronRight, Play } from 'lucide-react'
import axios from 'axios'
import AssessmentView from './AssessmentView'

export default function Assignments({ user }) {
  const [assignments, setAssignments] = useState([])
  const [loading, setLoading] = useState(true)
  const [showGenModal, setShowGenModal] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [classrooms, setClassrooms] = useState([])
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(null)

  useEffect(() => {
    fetchAssignments()
    if (user?.role === 'teacher') {
      fetchClassrooms()
    }
    
    const interval = setInterval(() => {
        axios.get('/api/v1/lms/assignments')
            .then(res => setAssignments(res.data))
            .catch(err => console.error(err))
    }, 5000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchAssignments = async () => {
    try {
        const res = await axios.get('/api/v1/lms/assignments')
        setAssignments(res.data)
    } catch (err) {
        console.error("Failed to fetch assignments", err)
    } finally {
        setLoading(false)
    }
  }

  const fetchClassrooms = async () => {
    try {
      const res = await axios.get('/api/v1/lms/classrooms')
      setClassrooms(res.data)
    } catch (err) {
      console.error("Failed to fetch classrooms", err)
    }
  }

  const handleGenerateExam = async (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    setGenerating(true)
    try {
        const classroomId = formData.get('classroom_id')
        await axios.post('/api/v1/lms/exams/generate', {
            title: formData.get('title'),
            topic: formData.get('topic'),
            num_questions: parseInt(formData.get('num')),
            classroom_id: classroomId || null,
            context_type: formData.get('context') || 'general'
        })
        setShowGenModal(false)
        fetchAssignments()
    } catch (err) {
        console.error("Exam generation failed", err)
        alert("Exam generation request failed. Ensure the backend is running.")
    } finally {
        setGenerating(false)
    }
  }

  if (selectedAssessmentId) {
    return <AssessmentView assessmentId={selectedAssessmentId} userId={user.id} onBack={() => setSelectedAssessmentId(null)} />
  }

  return (
    <div className="h-full flex flex-col p-2 space-y-6">
      <header className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-3xl font-medium tracking-tighter">Tests & <em className="text-white/60">Assignments</em></h2>
          <p className="text-sm text-white/40 mt-1">Construct and grade exams globally</p>
        </div>
        {user?.role === 'teacher' && (
          <button 
            onClick={() => setShowGenModal(true)}
            className="bg-white text-black pl-4 pr-5 py-2.5 rounded-full text-sm font-semibold flex items-center gap-2 hover:bg-white/90 transition-all shadow-xl"
          >
            <Plus size={18} /> Create Test
          </button>
        )}
      </header>

      <div className="flex-1 overflow-y-auto no-scrollbar pb-10">
        <div className="space-y-4">
          {loading ? (
             [1,2].map(i => <div key={i} className="h-32 liquid-glass rounded-2xl animate-pulse" />)
          ) : (
            <>
                {assignments.map((item, idx) => (
                    <motion.div 
                    key={item.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    onClick={() => setSelectedAssessmentId(item.id)}
                    className="liquid-glass rounded-3xl p-6 flex flex-col md:flex-row md:items-center justify-between border border-white/5 hover:bg-white/10 transition-colors group cursor-pointer"
                    >
                    <div className="flex items-center gap-5">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${item.status === 'active' ? 'bg-indigo-500/20 text-indigo-400' : 'bg-white/10 text-white/40'}`}>
                        {item.status === 'active' ? <Clock size={20} /> : <FileText size={20} />}
                        </div>
                        <div>
                        <h3 className="text-lg font-medium">{item.title}</h3>
                        <div className="text-xs text-white/40 font-medium tracking-wide mt-1">Class: {item.class}</div>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-6 mt-4 md:mt-0">
                        <div className="flex items-center gap-8 px-6 py-3 rounded-2xl bg-white/5 border border-white/5 group-hover:bg-white/10 transition-all">
                            <div className="text-center">
                            <div className="text-[10px] text-white/40 uppercase tracking-wider font-bold mb-1">Status</div>
                            <div className={`text-sm font-medium uppercase text-[10px] tracking-widest flex items-center justify-center gap-1.5 ${item.status === 'active' ? 'text-green-400' : 'text-orange-400'}`}>
                                {item.status === 'generating' && <div className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" />}
                                {item.status}
                            </div>
                            </div>
                            <div className="w-px h-8 bg-white/10"></div>
                            <div className="text-center">
                            <div className="text-[10px] text-white/40 uppercase tracking-wider font-bold mb-1">Turned In</div>
                            <div className="text-sm font-medium">{item.completions}</div>
                            </div>
                            <div className="w-px h-8 bg-white/10"></div>
                            <div className="text-center">
                            <div className="text-[10px] text-white/40 uppercase tracking-wider font-bold mb-1">Due Date</div>
                            <div className="text-sm font-medium text-orange-300/80">{item.due}</div>
                            </div>
                        </div>
                        <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-black opacity-0 group-hover:opacity-100 transition-all -translate-x-2 group-hover:translate-x-0 shadow-xl">
                            <Play size={16} fill="black" />
                        </div>
                    </div>
                    </motion.div>
                ))}
                {assignments.length === 0 && (
                    <div className="py-20 text-center text-white/10 italic text-sm">No active assessments in the archive.</div>
                )}
            </>
          )}
        </div>
      </div>

      <AnimatePresence>
        {showGenModal && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[300] bg-black/80 backdrop-blur-md flex items-center justify-center p-6">
                <motion.form 
                    initial={{ y: 20, scale: 0.95 }} animate={{ y: 0, scale: 1 }}
                    onSubmit={handleGenerateExam}
                    className="w-full max-w-lg liquid-glass-strong p-10 rounded-[2.5rem] border border-white/10 space-y-6"
                >
                    <div className="flex items-center gap-4 mb-2">
                        <div className="p-3 bg-indigo-500/20 text-indigo-400 rounded-2xl shadow-inner"><Sparkles size={24} /></div>
                        <h3 className="text-2xl font-medium">Cognitive AIGenerator</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="space-y-1">
                            <label className="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-2">Assessment Title</label>
                            <input required name="title" className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-sm focus:border-indigo-500/50 outline-none transition-all" placeholder="e.g. Midterm Mastery Check" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-2">Topic Focus</label>
                                <input name="topic" required className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-sm focus:border-indigo-500/50 outline-none transition-all" placeholder="Physics, Math, etc." />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-2">Question Count</label>
                                <input required name="num" type="number" min="1" max="20" defaultValue="5" className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-sm focus:border-indigo-500/50 outline-none transition-all" />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-2">Target Classroom</label>
                                <select name="classroom_id" className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-sm focus:border-indigo-500/50 outline-none appearance-none cursor-pointer">
                                    <option value="" className="bg-zinc-900">Select Classroom</option>
                                    {classrooms.map(c => (
                                        <option key={c.id} value={c.id} className="bg-zinc-900">{c.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-2">Knowledge Source</label>
                                <select name="context" className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-sm focus:border-indigo-500/50 outline-none appearance-none cursor-pointer">
                                    <option value="general" className="bg-zinc-900">Global Llama 3</option>
                                    <option value="document" className="bg-zinc-900">Classroom Materials (RAG)</option>
                                    <option value="mastery" className="bg-zinc-900">Student Weak Areas (Graph)</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-4 pt-4">
                        <button type="button" onClick={() => setShowGenModal(false)} className="flex-1 py-4 text-xs font-bold uppercase tracking-widest text-white/20 hover:text-white transition-colors">Abort</button>
                        <button type="submit" disabled={generating} className="flex-1 bg-white text-black py-4 rounded-2xl text-xs font-bold uppercase tracking-widest shadow-2xl hover:bg-indigo-100 disabled:opacity-50">
                            {generating ? 'Architecting...' : 'Construct Exam'}
                        </button>
                    </div>
                </motion.form>
            </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
