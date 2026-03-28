import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FileText, Plus, CheckCircle, Clock } from 'lucide-react'
import axios from 'axios'

export default function Assignments({ user }) {
  const [assignments, setAssignments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAssignments()
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

  return (
    <div className="h-full flex flex-col p-2 space-y-6">
      <header className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-3xl font-medium tracking-tighter">Tests & <em className="text-white/60">Assignments</em></h2>
          <p className="text-sm text-white/40 mt-1">Construct and grade exams globally</p>
        </div>
        <button className="bg-white text-black pl-4 pr-5 py-2.5 rounded-full text-sm font-semibold flex items-center gap-2 hover:bg-white/90 transition-all shadow-xl">
          <Plus size={18} /> Create Test
        </button>
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
                    className="liquid-glass rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between border border-white/5 hover:bg-white/10 transition-colors group cursor-pointer"
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
                    
                    <div className="flex items-center gap-8 mt-4 md:mt-0 px-6 py-3 rounded-2xl bg-white/5 border border-white/5">
                        <div className="text-center">
                        <div className="text-[10px] text-white/40 uppercase tracking-wider font-bold mb-1">Status</div>
                        <div className="text-sm font-medium uppercase text-[10px] tracking-widest">{item.status}</div>
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
                    </motion.div>
                ))}
                {assignments.length === 0 && (
                    <div className="py-20 text-center text-white/10 italic text-sm">No active assessments in the archive.</div>
                )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
