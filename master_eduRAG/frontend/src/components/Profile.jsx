import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import { 
  User as UserIcon, 
  Settings, 
  LogOut, 
  Mail, 
  GraduationCap, 
  Calendar,
  Zap,
  ShieldCheck,
  TrendingUp,
  BarChart2
} from 'lucide-react'

export default function Profile({ user, onUpdate, onLogout }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchUserStats = async () => {
      try {
        const response = await axios.get(`/api/v1/users/${user.id}`)
        setStats(response.data)
      } catch (err) {
        console.error("Failed to fetch profile stats", err)
      } finally {
        setLoading(false)
      }
    }
    fetchUserStats()
  }, [user.id])

  return (
    <div className="max-w-6xl mx-auto py-4 space-y-10">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="flex items-center gap-6">
          <div className="w-24 h-24 rounded-[2rem] liquid-glass-strong p-1 p-gradient-to-br from-white/20 to-transparent">
             <div className="w-full h-full rounded-[1.8rem] overflow-hidden">
                <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.email}`} alt="Avatar" className="w-full h-full object-cover" />
             </div>
          </div>
          <div>
            <h2 className="text-5xl font-medium tracking-tighter mb-2">{user.name}</h2>
            <div className="flex items-center gap-4 text-white/40">
                <span className="flex items-center gap-1.5 text-sm uppercase tracking-widest font-bold">
                    <GraduationCap size={14} /> {(user.student_level || 'student').replace('_', ' ')}
                </span>
                <span className="w-1 h-1 bg-white/20 rounded-full" />
                <span className="flex items-center gap-1.5 text-sm uppercase tracking-widest font-bold">
                    <Calendar size={14} /> Joined {new Date(stats?.user?.created_at || Date.now()).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}
                </span>
            </div>
          </div>
        </div>
        <div className="flex gap-3">
          <button className="liquid-glass px-6 py-3 rounded-2xl text-sm font-medium hover:bg-white/5 transition-all text-white/70 flex items-center gap-2 border border-white/5">
            <Settings size={16} />
            Edit Profile
          </button>
          <button 
            onClick={onLogout}
            className="bg-red-500/10 text-red-400 px-6 py-3 rounded-2xl text-sm font-semibold hover:bg-red-500/20 transition-all flex items-center gap-2 border border-red-500/10"
          >
            <LogOut size={16} />
            Log Out
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* PRIVATE INFO */}
        <div className="lg:col-span-4 space-y-6">
          <div className="liquid-glass-strong rounded-[2.5rem] p-8 space-y-8">
            <h3 className="text-xs font-bold tracking-widest uppercase text-white/30">Account Security</h3>
            
            <div className="space-y-6">
              <div className="flex items-center justify-between group">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center text-white/30 group-hover:text-white/60 transition-colors">
                        <Mail size={18} />
                    </div>
                    <div>
                        <div className="text-[10px] uppercase tracking-widest text-white/20">Email Address</div>
                        <div className="text-sm font-medium">{user.email}</div>
                    </div>
                </div>
                <div className="text-[10px] px-2 py-0.5 bg-green-500/10 text-green-400 rounded-md font-bold uppercase tracking-widest">Verified</div>
              </div>

              <div className="flex items-center justify-between group">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center text-white/30 group-hover:text-white/60 transition-colors">
                        <ShieldCheck size={18} />
                    </div>
                    <div>
                        <div className="text-[10px] uppercase tracking-widest text-white/20">Data Access</div>
                        <div className="text-sm font-medium">Scholarship Level</div>
                    </div>
                </div>
                <Zap size={14} className="text-white/20" />
              </div>
            </div>

            <div className="pt-8 border-t border-white/5">
                <p className="text-xs text-white/30 leading-relaxed italic">
                    Your cognitive archive is stored with AES-256 equivalent logic within the Studymines backend ecosystem.
                </p>
            </div>
          </div>
        </div>

        {/* ANALYTICS PREVIEW */}
        <div className="lg:col-span-8 liquid-glass rounded-[2.5rem] p-10 overflow-hidden relative">
          <div className="relative z-10 flex flex-col h-full">
            <div className="flex items-center justify-between mb-12">
               <div>
                  <h3 className="text-2xl font-medium tracking-tighter">Academic <em className="text-white/40">Engagement</em></h3>
                  <p className="text-white/30 text-sm mt-1">Cross-sectional performance analytics.</p>
               </div>
               <div className="p-3 bg-white/5 rounded-2xl liquid-glass">
                <BarChart2 size={24} className="text-white/40" />
               </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="space-y-4">
                    <div className="text-4xl font-semibold tracking-tighter">
                        {stats?.uploads_count || 0}
                    </div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/20">Total Artifacts</div>
                    <div className="h-1 w-full bg-white/5 rounded-full">
                        <motion.div initial={{width:0}} animate={{width: '60%'}} className="h-full bg-white/20" />
                    </div>
                </div>
                <div className="space-y-4">
                    <div className="text-4xl font-semibold tracking-tighter">
                        {(stats?.performance?.avg_score || 0).toFixed(1)}%
                    </div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/20">Mean Retention</div>
                    <div className="h-1 w-full bg-white/5 rounded-full">
                        <motion.div initial={{width:0}} animate={{width: `${stats?.performance?.avg_score || 0}%`}} className="h-full bg-white/60" />
                    </div>
                </div>
                <div className="space-y-4">
                    <div className="text-4xl font-semibold tracking-tighter">
                        {stats?.performance?.total_scores || 0}
                    </div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/20">Quiz Sessions</div>
                    <div className="h-1 w-full bg-white/5 rounded-full">
                        <motion.div initial={{width:0}} animate={{width: '40%'}} className="h-full bg-white/10" />
                    </div>
                </div>
            </div>

            <div className="mt-auto pt-12">
               <div className="p-6 bg-white/[0.02] border border-white/10 rounded-3xl flex items-center justify-between group hover:bg-white/[0.05] transition-all cursor-pointer">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-white text-black rounded-2xl flex items-center justify-center">
                        <TrendingUp size={24} />
                    </div>
                    <div>
                        <div className="font-semibold tracking-tight">Growth Archive</div>
                        <div className="text-xs text-white/40">Download your full academic progress report (PDF)</div>
                    </div>
                  </div>
                  <ChevronRight size={20} className="text-white/20 group-hover:translate-x-1 transition-transform" />
               </div>
            </div>
          </div>
          <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 blur-[120px] pointer-events-none" />
        </div>
      </div>
    </div>
  )
}

function ChevronRight({ size, className }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <path d="m9 18 6-6-6-6"/>
    </svg>
  )
}
