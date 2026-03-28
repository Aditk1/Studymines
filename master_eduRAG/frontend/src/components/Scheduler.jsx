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

export default function Scheduler({ user }) {
  const [reminders, setReminders] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeMeridian, setActiveMeridian] = useState(new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }))

  const milestones = [
    { title: 'Mid-term Algorithms', date: 'Oct 24', progress: 85, color: '#f59e0b' },
    { title: 'Project: RAG Pipeline', date: 'Nov 02', progress: 40, color: '#3b82f6' },
    { title: 'Thesis Submission', date: 'Dec 15', progress: 10, color: '#10b981' },
  ]

  useEffect(() => {
    fetchReminders()
  }, [])

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

  const handleMarkComplete = async (id) => {
    try {
        setReminders(prev => prev.filter(r => r.id !== id))
        // In a real app, we would call PATCH /api/v1/lms/reminders/{id} status=completed
    } catch (err) {
        console.error(err)
    }
  }

  return (
    <div className="h-full flex flex-col gap-8 p-4">
      <header className="flex items-center justify-between">
        <div>
           <h2 className="text-4xl font-medium tracking-tighter">Academic <em className="text-white/60">Chronos</em></h2>
           <p className="text-white/30 text-lg">Integrated scheduler & cognitive reminders.</p>
        </div>
        <div className="flex gap-4">
            <button className="h-12 w-12 rounded-2xl liquid-glass flex items-center justify-center text-white/40 hover:text-white transition-colors">
                <Bell size={20} />
            </button>
            <button className="flex items-center gap-2 bg-white text-black px-6 py-3 rounded-2xl font-bold hover:bg-white/90 transition-all shadow-xl">
                <Plus size={18} />
                Add Event
            </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1 overflow-hidden">
        {/* AGENDA COLUMN */}
        <div className="lg:col-span-12 xl:col-span-8 space-y-8 overflow-y-auto pr-2 custom-scrollbar">
            
            {/* TODAY HIGHLIGHT */}
            <div className="liquid-glass-strong rounded-[2.5rem] p-10 relative overflow-hidden group border border-white/10 shadow-2xl">
                <div className="relative z-10">
                    <div className="flex items-center gap-3 text-[10px] font-bold tracking-[0.4em] uppercase text-white/30 mb-8">
                        <CalendarIcon size={14} /> Current Meridian — {activeMeridian}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                        <div>
                             <h3 className="text-4xl font-medium tracking-tighter mb-4">Deep Focus <br /> <em className="text-white/60">Session</em></h3>
                             <p className="text-white/40 leading-relaxed mb-8">Your cognitive peak is predicted at 15:30 today. Recommended: "Advanced Graph Traversal" study block.</p>
                             <button className="bg-white/5 border border-white/10 hover:border-white/30 px-6 py-3 rounded-xl text-xs font-bold uppercase tracking-widest transition-all">
                                Adjust Schedule
                             </button>
                        </div>
                        <div className="flex items-center justify-center">
                            <div className="relative w-48 h-48">
                                <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                                    <circle cx="50" cy="50" r="45" stroke="rgba(255,255,255,0.05)" strokeWidth="6" fill="none" />
                                    <motion.circle 
                                        initial={{ strokeDasharray: "0 283" }}
                                        animate={{ strokeDasharray: "208 283" }}
                                        cx="50" cy="50" r="45" stroke="white" strokeWidth="6" fill="none" strokeLinecap="round" 
                                    />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <span className="text-3xl font-light">142</span>
                                    <span className="text-[10px] text-white/30 uppercase tracking-widest">Mins Left</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="absolute -right-24 -bottom-24 w-64 h-64 bg-white/10 rounded-full blur-[80px] opacity-30 group-hover:opacity-50 transition-all pointer-events-none" />
            </div>

            {/* UPCOMING REMINDERS */}
            <div className="space-y-4">
                <div className="flex items-center justify-between mb-6 px-2">
                    <h4 className="text-[10px] font-bold tracking-[0.3em] uppercase text-white/20">Today's Active Agenda</h4>
                    <span className="text-[10px] text-white/20 font-bold uppercase tracking-widest">{reminders.length} Pending</span>
                </div>
                <div className="grid grid-cols-1 gap-4">
                    {loading ? (
                        [1,2].map(i => <div key={i} className="h-24 liquid-glass rounded-3xl animate-pulse" />)
                    ) : (
                        <AnimatePresence>
                            {reminders.map((r) => (
                                <motion.div 
                                    key={r.id}
                                    layout
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, x: -50 }}
                                    whileHover={{ x: 10 }}
                                    className="p-6 rounded-3xl liquid-glass border border-white/5 flex items-center justify-between group cursor-pointer transition-all hover:bg-white/5"
                                >
                                    <div className="flex items-center gap-6">
                                        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center 
                                            ${r.priority === 'high' ? 'bg-red-500/10 text-red-400' : 'bg-white/5 text-white/30'}
                                        `}>
                                            <Clock size={20} />
                                        </div>
                                        <div>
                                            <h5 className="font-semibold text-white/90">{r.title}</h5>
                                            <div className="flex items-center gap-3 text-xs text-white/40 mt-1">
                                                <span className="flex items-center gap-1"><Clock size={12} /> {new Date(r.due_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                                                <span className="w-1 h-1 bg-white/20 rounded-full" />
                                                <span className="uppercase tracking-widest text-[9px]">{r.type}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <button 
                                            onClick={(e) => { e.stopPropagation(); handleMarkComplete(r.id); }}
                                            className="opacity-0 group-hover:opacity-100 transition-opacity bg-white text-black p-3 rounded-xl hover:scale-110 active:scale-95"
                                        >
                                            <CheckCircle size={18} />
                                        </button>
                                        <ChevronRight size={18} className="text-white/10 group-hover:text-white/40" />
                                    </div>
                                </motion.div>
                            ))}
                            {reminders.length === 0 && (
                                <div className="p-12 text-center text-white/20 italic text-sm">No pending reminders — meridian clear.</div>
                            )}
                        </AnimatePresence>
                    )}
                </div>
            </div>
        </div>

        {/* STATS / MILESTONES COLUMN */}
        <div className="lg:col-span-12 xl:col-span-4 space-y-8 overflow-y-auto pr-2 custom-scrollbar">
            <div className="p-8 rounded-[2rem] bg-indigo-600/10 border border-indigo-500/20 relative overflow-hidden group shadow-xl">
                <div className="relative z-10">
                    <h4 className="text-sm font-bold tracking-widest uppercase text-indigo-300 mb-6 flex items-center gap-2">
                        <AlertCircle size={16} /> Attention Required
                    </h4>
                    <p className="text-white/60 text-sm leading-relaxed mb-6 italic">
                        "Your performance in <strong>Cognitive Topology</strong> has dipped. AI suggests a brief review before the next quiz."
                    </p>
                    <button className="w-full bg-indigo-500 text-white py-3 rounded-xl text-xs font-bold uppercase tracking-widest hover:bg-indigo-400 transition-all shadow-lg active:scale-95">
                        Optimize Cycle
                    </button>
                </div>
            </div>

            <div className="space-y-6">
                 <h4 className="text-[10px] font-bold tracking-[0.3em] uppercase text-white/20 mb-6 px-2">Knowledge Milestones</h4>
                 <div className="space-y-4">
                    {milestones.map((m, idx) => (
                        <div key={idx} className="p-6 rounded-3xl bg-white/[0.03] border border-white/5 hover:bg-white/5 transition-all cursor-default">
                            <div className="flex items-center justify-between mb-4">
                                <h5 className="text-sm font-semibold">{m.title}</h5>
                                <span className="text-[10px] font-bold text-white/30 uppercase tracking-widest">{m.date}</span>
                            </div>
                            <div className="flex items-center gap-4">
                               <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                                    <motion.div 
                                        initial={{ width: 0 }}
                                        whileInView={{ width: `${m.progress}%` }}
                                        className="h-full"
                                        style={{ backgroundColor: m.color }}
                                    />
                               </div>
                               <span className="text-xs font-bold text-white/40">{m.progress}%</span>
                            </div>
                        </div>
                    ))}
                 </div>
            </div>

            <div className="mt-10 p-8 rounded-[2rem] liquid-glass border border-white/10 flex flex-col items-center text-center shadow-xl">
                <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center text-white/30 mb-6 shadow-inner">
                    <Target size={32} />
                </div>
                <h4 className="text-xl font-medium mb-3">Goal: Graph Saturation</h4>
                <p className="text-sm text-white/30 leading-relaxed mb-8 italic">Mastering cross-community links improves retention by 24%.</p>
                <div className="flex -space-x-3 mb-6">
                    {[1,2,3,4].map(i => (
                        <div key={i} className="w-8 h-8 rounded-full border-2 border-black bg-white/10 overflow-hidden shadow-lg">
                            <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=user${i}`} alt="user" />
                        </div>
                    ))}
                    <div className="w-8 h-8 rounded-full border-2 border-black bg-white text-black flex items-center justify-center text-[8px] font-bold shadow-lg">
                        +8
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  )
}
