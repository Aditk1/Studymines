import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  TrendingUp, 
  Clock, 
  BookOpen, 
  Award, 
  ArrowUpRight,
  MoreHorizontal,
  FileText,
  Calendar,
  MoreVertical,
  Eye,
  Edit,
  Trash2
} from 'lucide-react'

export default function Dashboard({ userId, onOpenArtifact, onOpenAssessment }) {
  const navigate = useNavigate()
  const [userData, setUserData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [assignments, setAssignments] = useState([])
  const [deleteModalId, setDeleteModalId] = useState(null)

  const confirmDelete = async () => {
    if (!deleteModalId) return;
    try {
      await axios.delete(`/api/v1/upload/${deleteModalId}`)
      setUserData(prev => ({
        ...prev,
        uploads: prev.uploads.filter(u => u.id !== deleteModalId),
        uploads_count: prev.uploads_count - 1
      }))
    } catch (err) {
      console.error("Failed to delete artifact", err)
    } finally {
      setDeleteModalId(null)
    }
  }

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const [userRes, assignRes] = await Promise.all([
            axios.get(`/api/v1/users/${userId}`),
            axios.get('/api/v1/lms/assignments')
        ])
        setUserData(userRes.data)
        setAssignments(assignRes.data)
        setError(null)
      } catch (err) {
        setError('Synchronizing local ecosystem...')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchUserData()
  }, [userId])

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-2 border-white/10 border-t-white/80 rounded-full animate-spin" />
        <p className="text-white/40 text-sm font-medium tracking-widest uppercase">Initializing Academy</p>
      </div>
    )
  }

  const stats = [
    { label: 'Artifacts', value: userData?.uploads_count || 0, icon: FileText, color: 'text-white' },
    { label: 'Accuracy', value: `${(userData?.performance?.avg_score || 0).toFixed(1)}%`, icon: TrendingUp, color: 'text-white/80' },
    { label: 'Sessions', value: userData?.performance?.total_scores || 0, icon: Clock, color: 'text-white/60' },
  ]

  return (
    <div className="max-w-6xl mx-auto py-4 space-y-10">
      {/* HEADER SECTION */}
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h2 className="text-5xl font-medium tracking-tighter mb-2">Welcome back, <em className="text-white/60">{userData?.user?.name || 'Scholar'}</em></h2>
          <p className="text-white/40 text-lg">Your cognitive archive is up to date.</p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => navigate('/explore-labs')}
            className="bg-white text-black px-6 py-3 rounded-2xl text-sm font-semibold hover:bg-white/90 transition-all flex items-center gap-2"
          >
            Explore Labs
            <ArrowUpRight size={16} />
          </button>
        </div>
      </header>

      {/* STATS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, idx) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="liquid-glass-strong rounded-[2.5rem] p-8 group hover:scale-[1.02] transition-transform duration-500"
          >
            <div className="flex items-center justify-between mb-8">
              <div className="w-12 h-12 liquid-glass rounded-2xl flex items-center justify-center text-white/50 group-hover:text-white transition-colors">
                <stat.icon size={24} />
              </div>
              {idx === 0 && (
                <button className="text-white/20 hover:text-white/40">
                  <MoreHorizontal size={20} />
                </button>
              )}
            </div>
            <div className="text-[10px] tracking-[0.2em] font-bold uppercase text-white/30 mb-1">{stat.label}</div>
            <div className={`text-4xl font-semibold ${stat.color}`}>{stat.value}</div>
          </motion.div>
        ))}
      </div>

      {/* RECENT ACTIVITY & GROWTH */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* COLLECTIONS (Left) */}
        <div className="lg:col-span-8 liquid-glass rounded-[2.5rem] p-10 overflow-hidden relative">
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-2xl font-medium tracking-tighter">Recent <em className="text-white/60">Artifacts</em></h3>
              <button 
                onClick={() => navigate('/library/artifacts')}
                className="text-sm text-white/40 hover:text-white/80 transition-colors flex items-center gap-2"
              >
                View Library
                <ArrowUpRight size={14} />
              </button>
            </div>

            {userData?.uploads && userData.uploads.length > 0 ? (
              <div className="space-y-4">
                {userData.uploads.slice(0, 4).map((upload, idx) => (
                  <div 
                    key={idx} 
                    onClick={() => onOpenArtifact(upload.id)}
                    className="flex items-center justify-between p-5 rounded-3xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.05] cursor-pointer transition-all group relative"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 liquid-glass rounded-xl flex items-center justify-center text-white/40 group-hover:text-white/80 transition-colors">
                        <BookOpen size={18} />
                      </div>
                      <div>
                        <h4 className="font-medium text-white/90">{upload.subject || 'Untitled'}</h4>
                        <p className="text-xs text-white/30 tracking-wider uppercase mt-0.5">{upload.topic || 'General Archive'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-right">
                      <div>
                        <div className="text-xs text-white/40">{new Date(upload.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</div>
                        <button 
                          onClick={(e) => { e.stopPropagation(); onOpenArtifact(upload.id); }}
                          className="text-xs text-white/60 font-semibold hover:text-white mt-1 opacity-0 group-hover:opacity-100 transition-all font-poppins"
                        >
                          Study Now
                        </button>
                      </div>
                      
                      {/* Direct Delete Button */}
                      <button 
                        onClick={(e) => { e.stopPropagation(); setDeleteModalId(upload.id) }}
                        className="p-2 text-white/40 hover:text-red-400 rounded-full hover:bg-red-500/10 transition-colors opacity-0 group-hover:opacity-100"
                        title="Delete Artifact"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-20 flex flex-col items-center text-center">
                <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center text-white/20 mb-4">
                  <BookOpen size={32} />
                </div>
                <p className="text-white/40 max-w-xs">No artifacts discovered yet. Start by generating a study package.</p>
              </div>
            )}
          </div>
          
          {/* DECORATIVE LIGHT */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 blur-[100px] pointer-events-none" />
        </div>

        {/* PENDING ASSIGNMENTS (New Center Section) */}
        <div className="lg:col-span-8 liquid-glass rounded-[2.5rem] p-10 overflow-hidden relative">
            <div className="relative z-10">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-2xl font-medium tracking-tighter">Academic <br /> <em className="text-white/60">Milestones</em></h3>
                    <div className="px-4 py-1.5 rounded-full bg-white/5 border border-white/5 text-[10px] font-bold uppercase tracking-[0.2em]">Pending Assessments</div>
                </div>

                <div className="space-y-4">
                    {assignments.slice(0, 3).map((assign, i) => (
                        <div key={i} className="flex items-center justify-between p-6 rounded-3xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.05] transition-all group">
                            <div className="flex items-center gap-5">
                                <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center group-hover:bg-indigo-500/20 transition-colors">
                                    <FileText size={20} />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-lg">{assign.title}</h4>
                                    <p className="text-xs text-white/30 tracking-widest uppercase font-bold mt-1">{assign.class}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-10">
                                <div className="text-right hidden sm:block">
                                    <div className="text-[10px] text-white/20 uppercase tracking-widest font-bold mb-1">Due Date</div>
                                    <div className="text-sm font-medium text-orange-400/80">{assign.due}</div>
                                </div>
                                <button 
                                    onClick={() => onOpenAssessment(assign.id)}
                                    className="px-6 py-3 rounded-2xl bg-white text-black text-xs font-bold uppercase tracking-widest shadow-xl hover:bg-white/90 active:scale-95 transition-all"
                                >
                                    Launch Exam
                                </button>
                            </div>
                        </div>
                    ))}
                    {assignments.length === 0 && (
                        <div className="py-20 flex flex-col items-center text-center">
                            <Clock size={32} className="text-white/10 mb-4" />
                            <p className="text-white/20 italic text-sm">No assessments architected for your current cohort.</p>
                        </div>
                    )}
                </div>
            </div>
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-indigo-500/5 blur-[120px] pointer-events-none" />
        </div>

        {/* PERFORMANCE (Right) */}
        <div className="lg:col-span-4 space-y-6">
          <div className="liquid-glass rounded-[2rem] p-8 relative overflow-hidden group">
            <h4 className="text-xs font-bold tracking-widest uppercase text-white/30 mb-6">Expertise Bloom</h4>
            <div className="flex items-center justify-center h-40">
              {/* SVG Radial Chart */}
              <div className="relative w-32 h-32">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="64"
                    cy="64"
                    r="60"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    className="text-white/5"
                  />
                  <motion.circle
                    initial={{ strokeDashoffset: 377 }}
                    animate={{ strokeDashoffset: 377 - (377 * (userData?.performance?.avg_score || 72) / 100) }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    cx="64"
                    cy="64"
                    r="60"
                    stroke="currentColor"
                    strokeWidth="8"
                    strokeDasharray="377"
                    fill="transparent"
                    className="text-white/60"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold">{(userData?.performance?.avg_score || 0).toFixed(0)}<em>%</em></span>
                </div>
              </div>
            </div>
            <p className="text-xs text-white/40 text-center mt-6 leading-relaxed">
              Based on active recall metrics across <strong>{userData?.performance?.total_scores || 0}</strong> artifacts.
            </p>
          </div>

          <div className="liquid-glass-strong rounded-[2rem] p-8 text-center bg-gradient-to-br from-white/10 to-transparent border border-white/10">
            <div className="w-12 h-12 bg-white text-black rounded-full flex items-center justify-center mx-auto mb-4">
              <Award size={24} />
            </div>
            <h4 className="text-lg font-medium tracking-tight mb-2">Academic Rank</h4>
            <div className="text-3xl font-bold mb-4 tracking-tighter">Gold Tier</div>
            <button className="w-full bg-white/10 hover:bg-white/20 py-3 rounded-xl text-xs font-bold tracking-widest uppercase transition-all">
              View Milestones
            </button>
          </div>
        </div>
      </div>

      {/* CUSTOM DELETE MODAL */}
      <AnimatePresence>
        {deleteModalId && (
          <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }} 
              exit={{ opacity: 0 }}
              onClick={() => setDeleteModalId(null)}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm cursor-pointer"
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-sm liquid-glass-strong border border-white/10 rounded-3xl p-8 shadow-2xl text-center z-10"
            >
              <div className="w-16 h-16 rounded-full bg-red-500/10 text-red-400 flex items-center justify-center mx-auto mb-6">
                <Trash2 size={24} />
              </div>
              <h3 className="text-xl font-medium tracking-tight mb-2">Delete Artifact?</h3>
              <p className="text-sm text-white/60 mb-8 leading-relaxed">
                Are you sure you want to permanently delete this study artifact from your cognitive archive? This action cannot be reversed.
              </p>
              <div className="flex items-center gap-3">
                <button 
                  onClick={() => setDeleteModalId(null)}
                  className="flex-1 py-3 px-4 rounded-xl font-semibold text-sm bg-white/5 hover:bg-white/10 transition-colors"
                >
                  Cancel
                </button>
                <button 
                  onClick={confirmDelete}
                  className="flex-1 py-3 px-4 rounded-xl font-semibold text-sm bg-red-500 hover:bg-red-600 text-white transition-colors"
                >
                  Delete
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  )
}
