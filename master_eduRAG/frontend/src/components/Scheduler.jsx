/**
 * Reminder and schedule management view.
 */
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { 
  Calendar as CalendarIcon, 
  Clock, 
  Plus, 
  CheckCircle2, 
  AlertCircle, 
  Target,
  ChevronRight,
  Bell,
  CheckCircle
} from 'lucide-react'

/**
 * Reminder and schedule management view.
 */
export default function Scheduler({ user }) {
  const [reminders, setReminders] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeMeridian, setActiveMeridian] = useState(new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }))
  const [showAddModal, setShowAddModal] = useState(false)
  const [isOptimizing, setIsOptimizing] = useState(false)
  const [minsRemaining, setMinsRemaining] = useState(142)
  const [newEvent, setNewEvent] = useState({ title: '', reminder_type: 'study', priority: 'medium', due_at: new Date().toISOString().slice(0, 16) })

  useEffect(() => {
    fetchReminders()
    const timer = setInterval(() => {
        setMinsRemaining(prev => prev > 0 ? prev - 1 : 0)
    }, 60000)
    return () => clearInterval(timer)
  }, [])

  const milestones = [
    { title: 'Mid-term Algorithms', date: 'Oct 24', progress: 85, color: '#f59e0b' },
    { title: 'Project: RAG Pipeline', date: 'Nov 02', progress: 40, color: '#3b82f6' },
    { title: 'Thesis Submission', date: 'Dec 15', progress: 10, color: '#10b981' },
  ]

  const fetchReminders = async () => {
    try {
      const res = await axios.get('/api/v1/lms/reminders')
      setReminders(res.data)
    } catch (err) {
      console.error("Failed to fetch reminders", err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddEvent = async () => {
      try {
          await axios.post('/api/v1/lms/reminders', newEvent)
          setShowAddModal(false)
          fetchReminders()
          setNewEvent({ title: '', reminder_type: 'study', priority: 'medium', due_at: new Date().toISOString().slice(0, 16) })
      } catch (err) {
          console.error(err)
      }
  }

  const handleMarkComplete = async (id) => {
    try {
        setReminders(prev => prev.filter(r => r.id !== id))
        // Real PATCH call would go here
    } catch (err) {
        console.error(err)
    }
  }

  const handleOptimizeCycle = () => {
      setIsOptimizing(true)
      setTimeout(() => {
          setIsOptimizing(false)
          alert("Neural Rebalancing Complete: High-focus sessions shifted to 16:00 to align with cognitive recovery.")
      }, 3000)
  }

  if (loading) return <div className="h-full flex items-center justify-center text-white/20 uppercase tracking-widest text-xs font-bold">Synchronizing Chronos...</div>

  return (
    <div className="h-full flex flex-col gap-8 p-4 relative">
      <header className="flex items-center justify-between">
        <div>
           <h2 className="text-4xl font-medium tracking-tighter">Academic <em className="text-white/60">Chronos</em></h2>
           <p className="text-white/30 text-lg">Integrated scheduler & cognitive reminders.</p>
        </div>
        <div className="flex gap-4">
            <button className="h-12 w-12 rounded-2xl liquid-glass flex items-center justify-center text-white/40 hover:text-white transition-colors relative">
                <Bell size={20} />
                <span className="absolute top-3 right-3 w-2 h-2 bg-indigo-500 rounded-full animate-ping" />
            </button>
            <button 
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 bg-white text-black px-6 py-3 rounded-2xl font-bold hover:bg-white/90 transition-all shadow-[0_15px_30px_rgba(255,255,255,0.1)] hover:scale-[1.02]"
            >
                <Plus size={18} />
                Add Event
            </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1 overflow-hidden">
        {/* AGENDA COLUMN */}
        <div className="lg:col-span-12 xl:col-span-8 space-y-8 overflow-y-auto pr-2 custom-scrollbar">
            
            {/* TODAY HIGHLIGHT */}
            <div className="liquid-glass-strong rounded-[2.5rem] p-10 relative overflow-hidden group border border-white/10 shadow-[0_50px_100px_rgba(0,0,0,0.5)]">
                <div className="relative z-10">
                    <div className="flex items-center gap-3 text-[10px] font-bold tracking-[0.4em] uppercase text-white/30 mb-8">
                        <CalendarIcon size={14} /> Current Meridian — {activeMeridian}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                        <div>
                             <h3 className="text-4xl font-medium tracking-tighter mb-4 leading-tight">Deep Focus <br /> <em className="text-white/60">Session</em></h3>
                             <p className="text-white/40 leading-relaxed mb-8">Your cognitive peak is predicted at 15:30 today. Recommended: <strong className="text-white/70">"Advanced Graph Traversal"</strong> study block.</p>
                             <button className="bg-white/5 border border-white/10 hover:border-white/30 hover:bg-white/10 px-8 py-4 rounded-xl text-xs font-bold uppercase tracking-widest transition-all">
                                Adjust Schedule
                             </button>
                        </div>
                        <div className="flex items-center justify-center">
                            <div className="relative w-48 h-48">
                                <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90 drop-shadow-[0_0_20px_rgba(255,255,255,0.1)]">
                                    <circle cx="50" cy="50" r="45" stroke="rgba(255,255,255,0.05)" strokeWidth="6" fill="none" />
                                    <motion.circle 
                                        initial={{ strokeDashoffset: 283 }}
                                        animate={{ strokeDashoffset: 283 - (283 * (minsRemaining / 180)) }}
                                        cx="50" cy="50" r="45" stroke="white" strokeWidth="6" fill="none" strokeDasharray="283" strokeLinecap="round" 
                                    />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <span className="text-4xl font-light">{minsRemaining}</span>
                                    <span className="text-[10px] text-white/30 uppercase tracking-[0.3em] mt-1">Mins Left</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="absolute -right-24 -bottom-24 w-64 h-64 bg-indigo-500/10 rounded-full blur-[80px] opacity-30 group-hover:opacity-50 transition-all pointer-events-none" />
            </div>

            {/* UPCOMING REMINDERS */}
            <div className="space-y-4">
                <div className="flex items-center justify-between mb-6 px-2">
                    <h4 className="text-[10px] font-bold tracking-[0.3em] uppercase text-white/20">Today's Active Agenda</h4>
                    <span className="text-[10px] text-white/20 font-bold uppercase tracking-widest px-3 py-1 bg-white/5 rounded-full">{reminders.length} Pending</span>
                </div>
                <div className="grid grid-cols-1 gap-4">
                    <AnimatePresence>
                        {reminders.map((r) => (
                            <motion.div 
                                key={r.id}
                                layout
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, x: -50 }}
                                whileHover={{ x: 10 }}
                                className="p-6 rounded-[2rem] bg-white/[0.02] border border-white/5 flex items-center justify-between group cursor-pointer transition-all hover:bg-white/5"
                            >
                                <div className="flex items-center gap-6">
                                    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center border transition-colors
                                        ${r.priority === 'high' ? 'bg-red-500/10 border-red-500/20 text-red-400' : 'bg-white/5 border-white/5 text-white/30'}
                                    `}>
                                        <Clock size={24} />
                                    </div>
                                    <div>
                                        <h5 className="font-semibold text-white/90 text-lg tracking-tight">{r.title}</h5>
                                        <div className="flex items-center gap-3 text-xs text-white/40 mt-1">
                                            <span className="flex items-center gap-1 font-medium"><Clock size={12} /> {new Date(r.due_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                                            <span className="w-1 h-1 bg-white/20 rounded-full" />
                                            <span className="uppercase tracking-[0.2em] text-[9px] font-bold text-white/20">{r.type}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <button 
                                        onClick={(e) => { e.stopPropagation(); handleMarkComplete(r.id); }}
                                        className="opacity-0 group-hover:opacity-100 transition-all bg-white text-black p-4 rounded-2xl hover:scale-110 active:scale-95 shadow-xl"
                                    >
                                        <CheckCircle2 size={18} />
                                    </button>
                                    <ChevronRight size={18} className="text-white/10 group-hover:text-white/40 transition-colors" />
                                </div>
                            </motion.div>
                        ))}
                        {reminders.length === 0 && !loading && (
                            <motion.div 
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                className="p-16 text-center rounded-[3rem] border border-dashed border-white/5"
                            >
                                <div className="text-white/10 text-4xl mb-4 italic">✨</div>
                                <div className="text-white/20 italic text-sm tracking-widest font-medium">No pending reminders — meridian clear.</div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>

        {/* STATS / MILESTONES COLUMN */}
        <div className="lg:col-span-12 xl:col-span-4 space-y-8 overflow-y-auto pr-2 custom-scrollbar">
            <div className="p-10 rounded-[2.5rem] bg-indigo-600/10 border border-indigo-500/20 relative overflow-hidden group shadow-[0_30px_60px_rgba(79,70,229,0.1)]">
                <div className="relative z-10">
                    <h4 className="text-xs font-bold tracking-[0.3em] uppercase text-indigo-300 mb-6 flex items-center gap-2">
                        <AlertCircle size={16} /> Attention Required
                    </h4>
                    <p className="text-white/60 text-sm leading-relaxed mb-8 italic">
                        "Your performance in <strong className="text-white/80">Cognitive Topology</strong> has dipped. Studymines suggests a brief review before the next quiz cycle to maintain 85% mastery."
                    </p>
                    <button 
                        onClick={handleOptimizeCycle}
                        disabled={isOptimizing}
                        className="w-full bg-indigo-600 text-white py-4 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] hover:bg-indigo-500 transition-all shadow-[0_15px_30px_rgba(79,70,229,0.3)] active:scale-95 disabled:opacity-50"
                    >
                        {isOptimizing ? "Calibrating..." : "Optimize Cycle"}
                    </button>
                </div>
                <motion.div 
                    animate={isOptimizing ? { rotate: 360 } : {}}
                    transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
                    className="absolute -right-12 -top-12 w-32 h-32 bg-indigo-500/20 rounded-full blur-[40px] pointer-events-none" 
                />
            </div>

            <div className="p-8 liquid-glass rounded-[2.5rem] border border-white/5 space-y-8 shadow-2xl">
                 <h4 className="text-[10px] font-bold tracking-[0.3em] uppercase text-white/20 px-2 flex items-center justify-between">
                    <span>Knowledge Milestones</span>
                    <Plus size={12} className="cursor-pointer hover:text-white" />
                 </h4>
                 <div className="space-y-6">
                    {milestones.map((m, idx) => (
                        <div key={idx} className="space-y-3 px-2">
                            <div className="flex items-center justify-between">
                                <h5 className="text-xs font-bold text-white/60 tracking-tight">{m.title}</h5>
                                <span className="text-[9px] font-black text-white/20 uppercase tracking-widest">{m.date}</span>
                            </div>
                            <div className="flex items-center gap-4">
                               <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                                    <motion.div 
                                        initial={{ width: 0 }}
                                        whileInView={{ width: `${m.progress}%` }}
                                        className="h-full shadow-[0_0_10px_currentColor]"
                                        style={{ backgroundColor: m.color, color: m.color }}
                                    />
                               </div>
                               <span className="text-[10px] font-black text-white/30">{m.progress}%</span>
                            </div>
                        </div>
                    ))}
                 </div>
            </div>

            <div className="p-10 rounded-[2.5rem] liquid-glass-strong border border-white/10 flex flex-col items-center text-center shadow-2xl group transition-all hover:bg-white/[0.04]">
                <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center text-white/20 mb-6 shadow-inner group-hover:text-indigo-400 transition-colors">
                    <Target size={32} />
                </div>
                <h4 className="text-xl font-medium mb-3 tracking-tight">Goal: Concept Saturation</h4>
                <p className="text-xs text-white/30 leading-relaxed mb-8 italic">Mastering cross-community links improves long-term retention by 24%.</p>
                <div className="flex -space-x-3 mb-4">
                    {[1,2,3,4].map(i => (
                        <div key={i} className="w-9 h-9 rounded-full border-2 border-[#121212] bg-white/10 overflow-hidden shadow-xl ring-1 ring-white/5">
                            <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=user${i + 13}`} alt="user" />
                        </div>
                    ))}
                    <div className="w-9 h-9 rounded-full border-2 border-[#121212] bg-white text-black flex items-center justify-center text-[10px] font-black shadow-xl ring-1 ring-white/5">
                        +8
                    </div>
                </div>
                <span className="text-[9px] font-bold text-white/20 uppercase tracking-widest">Global Peer Milestone</span>
            </div>
        </div>
      </div>

      {/* ADD EVENT MODAL */}
      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-[1000] flex items-center justify-center p-6">
            <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                onClick={() => setShowAddModal(false)}
                className="absolute inset-0 bg-black/80 backdrop-blur-xl"
            />
            <motion.div 
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="relative w-full max-w-md liquid-glass-strong p-10 rounded-[3rem] border border-white/10 shadow-[0_50px_100px_rgba(0,0,0,0.8)]"
            >
                <div className="flex items-center gap-4 mb-8">
                    <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center text-white/40">
                        <CalendarIcon size={24} />
                    </div>
                    <div>
                        <h3 className="text-2xl font-medium tracking-tight">Add Chronos Event</h3>
                        <p className="text-white/30 text-xs mt-1">Manual entry for cognitive tracking.</p>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-[9px] font-black uppercase tracking-widest text-white/20 ml-2">Event Title</label>
                        <input 
                            type="text" 
                            placeholder="e.g. LLM Community Review"
                            value={newEvent.title}
                            onChange={(e) => setNewEvent({...newEvent, title: e.target.value})}
                            className="w-full bg-white/5 border border-white/10 rounded-2xl p-5 text-sm focus:outline-none focus:border-white/40 transition-all font-medium"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-[9px] font-black uppercase tracking-widest text-white/20 ml-2">Type</label>
                            <select 
                                value={newEvent.reminder_type}
                                onChange={(e) => setNewEvent({...newEvent, reminder_type: e.target.value})}
                                className="w-full bg-white/5 border border-white/10 rounded-2xl p-5 text-sm focus:outline-none appearance-none"
                            >
                                <option value="study" className="bg-[#121212]">Study Block</option>
                                <option value="quiz" className="bg-[#121212]">Quiz Cycle</option>
                                <option value="submission" className="bg-[#121212]">Submission</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-[9px] font-black uppercase tracking-widest text-white/20 ml-2">Priority</label>
                            <select 
                                value={newEvent.priority}
                                onChange={(e) => setNewEvent({...newEvent, priority: e.target.value})}
                                className="w-full bg-white/5 border border-white/10 rounded-2xl p-5 text-sm focus:outline-none appearance-none"
                            >
                                <option value="low" className="bg-[#121212]">Low</option>
                                <option value="medium" className="bg-[#121212]">Medium</option>
                                <option value="high" className="bg-[#121212]">Critical</option>
                            </select>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <label className="text-[9px] font-black uppercase tracking-widest text-white/20 ml-2">Target Meridian</label>
                        <input 
                            type="datetime-local"
                            value={newEvent.due_at}
                            onChange={(e) => setNewEvent({...newEvent, due_at: e.target.value})}
                            className="w-full bg-white/5 border border-white/10 rounded-2xl p-5 text-sm focus:outline-none focus:border-white/40 transition-all font-medium text-white/60"
                        />
                    </div>
                </div>

                <div className="flex gap-4 mt-12">
                    <button 
                        onClick={() => setShowAddModal(false)}
                        className="flex-1 py-5 text-xs font-bold uppercase tracking-widest text-white/20 hover:text-white transition-all"
                    >
                        Close
                    </button>
                    <button 
                        onClick={handleAddEvent}
                        className="flex-1 bg-white text-black py-5 rounded-[1.5rem] text-xs font-black uppercase tracking-[0.2em] shadow-xl hover:scale-[1.02] transition-all"
                    >
                        Integrate
                    </button>
                </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
