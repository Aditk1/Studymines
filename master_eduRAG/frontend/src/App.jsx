import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  BarChart3, 
  Upload as UploadIcon, 
  LayoutDashboard, 
  TrendingUp, 
  Settings,
  Bell,
  Search,
  Menu,
  Sparkles,
  Beaker,
  User as UserIcon
} from 'lucide-react'
import Upload from './components/Upload'
import Dashboard from './components/Dashboard'
import Leaderboard from './components/Leaderboard'
import StudyLab from './components/StudyLab'
import Research from './components/Research'
import Auth from './components/Auth'
import Profile from './components/Profile'
import Chatbot from './components/Chatbot'
import Classrooms from './components/Classrooms'
import Analytics from './components/Analytics'
import Content from './components/Content'
import GlobalChat from './components/GlobalChat'
import Assignments from './components/Assignments'
import Members from './components/Members'
import { FileText, Users, MessageSquare, BookOpen } from 'lucide-react'
import axios from 'axios'

function App() {
  const [user, setUser] = useState(null)
  const [currentPage, setCurrentPage] = useState('upload')
  const [selectedUploadId, setSelectedUploadId] = useState(null)

  // Configure global axios interceptor for auth
  useEffect(() => {
    const token = localStorage.getItem('studymines_token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  }, [])

  // Auto-login logic (checking localStorage for saved user)
  useEffect(() => {
    const savedUser = localStorage.getItem('studymines_user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
  }, [])

  const handleLogin = (userData, token) => {
    setUser(userData)
    localStorage.setItem('studymines_user', JSON.stringify(userData))
    if (token) {
      localStorage.setItem('studymines_token', token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('studymines_user')
    localStorage.removeItem('studymines_token')
    delete axios.defaults.headers.common['Authorization']
    setCurrentPage('upload')
  }

  const navItems = user?.role === 'teacher' 
    ? [
        { id: 'classrooms', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'content', label: 'Content', icon: BookOpen },
        { id: 'chat', label: 'Discussions', icon: MessageSquare },
        { id: 'assignments', label: 'Assignments', icon: FileText },
        { id: 'analytics', label: 'Insights', icon: BarChart3 },
        { id: 'members', label: 'Members', icon: Users },
      ]
    : [
        { id: 'dashboard', label: 'Academy', icon: LayoutDashboard },
        { id: 'upload', label: 'Generate', icon: UploadIcon },
        { id: 'classrooms', label: 'My Classes', icon: UserIcon },
        { id: 'leaderboard', label: 'Ecosystem', icon: TrendingUp },
        { id: 'research', label: 'Laboratory', icon: Beaker },
      ]

  const openArtifact = (id) => {
    setSelectedUploadId(id)
    setCurrentPage('study-lab')
  }

  if (!user) {
    return <Auth onLogin={handleLogin} />
  }

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-black text-white font-poppins selection:bg-white/20">
      {/* BACKGROUND VIDEO */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="fixed inset-0 z-0 h-full w-full object-cover opacity-60 pointer-events-none"
      >
        <source src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260315_073750_51473149-4350-4920-ae24-c8214286f323.mp4" type="video/mp4" />
      </video>

      {/* OVERLAY MASK */}
      <div className="fixed inset-0 z-[1] bg-black/20 pointer-events-none" />

      {/* CONTENT WRAPPER */}
      <div className="relative z-10 flex flex-col lg:flex-row h-screen overflow-hidden lg:p-6 gap-6">

        {/* LEFT SIDEBAR (DESKTOP) */}
        <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="hidden lg:flex flex-col w-[260px] h-full liquid-glass rounded-3xl p-6 shadow-2xl shrink-0"
        >
          <div className="flex items-center gap-3 mb-10">
            <img src="/logo.png" alt="Studymines" className="w-8 h-8 pointer-events-none" />
            <span className="text-2xl font-semibold tracking-tighter lowercase">Study<em>mines</em></span>
          </div>

          <div className="flex-1 flex flex-col gap-2 overflow-y-auto custom-scrollbar pr-2">
             {navItems.map((item) => (
               <button
                 key={item.id}
                 onClick={() => {
                   setCurrentPage(item.id)
                   setSelectedUploadId(null)
                 }}
                 className={`
                   flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all duration-300
                   ${(currentPage === item.id || (currentPage === 'study-lab' && item.id === 'dashboard'))
                     ? 'bg-white/10 text-white shadow-[0_0_15px_rgba(255,255,255,0.1)]' 
                     : 'text-white/40 hover:text-white/70 hover:bg-white/5'}
                 `}
               >
                 <item.icon size={18} />
                 {item.label}
               </button>
             ))}
          </div>

          <div className="mt-8 pt-6 border-t border-white/10 flex items-center justify-between">
            <button 
              onClick={() => setCurrentPage('profile')}
              className="flex items-center gap-3 hover:bg-white/5 p-2 rounded-xl transition-colors min-w-0"
            >
              <div className="h-10 w-10 shrink-0 overflow-hidden rounded-full liquid-glass border border-white/10">
                <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.email}`} alt="User" />
              </div>
              <div className="text-left truncate">
                <div className="text-sm font-semibold text-white/90 truncate">{(user.name || 'User').split(' ')[0]}</div>
                <div className="text-[10px] text-white/40 uppercase tracking-widest">{user.role}</div>
              </div>
            </button>
            <button className="h-10 w-10 shrink-0 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 transition-colors text-white/40 hover:text-white">
              <Bell size={18} />
            </button>
          </div>
        </motion.div>
        
        {/* CENTER PANEL: MAIN APP VIEW */}
        <div className="flex-1 flex flex-col h-full min-w-0">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="liquid-glass-strong flex-1 rounded-3xl overflow-hidden flex flex-col p-6 shadow-2xl"
          >
            {/* MOBILE TOP NAV (HIDDEN ON DESKTOP) */}
            <nav className="flex lg:hidden items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <img src="/logo.png" alt="Studymines" className="w-8 h-8 pointer-events-none" />
                <span className="text-xl font-semibold tracking-tighter lowercase">Study<em>mines</em></span>
              </div>
              <button className="w-10 h-10 flex items-center justify-center rounded-full bg-white/5 text-white/70">
                <Menu size={20} />
              </button>
            </nav>

            {/* MAIN SCROLLABLE CONTENT AREA */}
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentPage + (selectedUploadId || '')}
                  initial={{ opacity: 0, scale: 0.98, x: -10 }}
                  animate={{ opacity: 1, scale: 1, x: 0 }}
                  exit={{ opacity: 0, scale: 1.02, x: 10 }}
                  transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                  className="h-full"
                >
                  {currentPage === 'upload' && <Upload userId={user.id} onOpenArtifact={(id) => openArtifact(id)} />}
                  {currentPage === 'dashboard' && <Dashboard userId={user.id} onOpenArtifact={(id) => openArtifact(id)} />}
                  {currentPage === 'classrooms' && <Classrooms user={user} onOpenArtifact={(id) => openArtifact(id)} />}
                  {currentPage === 'analytics' && <Analytics user={user} />}
                  {currentPage === 'content' && <Content user={user} onOpenArtifact={(id) => openArtifact(id)} />}
                  {currentPage === 'chat' && <GlobalChat user={user} />}
                  {currentPage === 'assignments' && <Assignments user={user} />}
                  {currentPage === 'members' && <Members user={user} />}
                  {currentPage === 'leaderboard' && <Leaderboard />}
                  {currentPage === 'research' && <Research />}
                  {currentPage === 'profile' && <Profile user={user} onLogout={handleLogout} />}
                  {currentPage === 'study-lab' && (
                    <StudyLab 
                      uploadId={selectedUploadId} 
                      userId={user.id} 
                      onBack={() => setCurrentPage(user?.role === 'teacher' ? 'classrooms' : 'dashboard')} 
                    />
                  )}
                </motion.div>
              </AnimatePresence>
            </div>
          </motion.div>
        </div>

        {/* RIGHT PANEL: ECOSYSTEM STATS (DESKTOP ONLY) */}
        <div className="hidden lg:flex flex-col w-[360px] h-full gap-6">
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="liquid-glass rounded-3xl p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-semibold tracking-widest uppercase text-white/50">Core Metrics</h3>
              <Sparkles size={16} className="text-white/40" />
            </div>
            
            <div className="space-y-4">
              <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                <div className="text-xs text-white/40 mb-1">Knowledge Retained</div>
                <div className="text-2xl font-semibold">84.2%</div>
                <div className="h-1 w-full bg-white/5 rounded-full mt-3 overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: '84.2%' }}
                    className="h-full bg-white/40"
                  />
                </div>
              </div>
              <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                <div className="text-xs text-white/40 mb-1">Study Hours</div>
                <div className="text-2xl font-semibold">124.5<em> hrs</em></div>
              </div>
            </div>
          </motion.div>

          {user?.role === 'teacher' && (
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="liquid-glass rounded-3xl p-6 flex flex-col"
            >
              <nav className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                  <h3 className="font-medium tracking-tighter">Student Distribution</h3>
                  <div className="px-2 py-0.5 rounded-full bg-white/10 text-[10px] font-bold tracking-wider uppercase">Live</div>
                </div>
              </nav>

              <div className="flex-1 flex items-center justify-center p-8 bg-white/5 rounded-2xl border border-white/5">
                 <div className="relative w-40 h-40">
                  <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                    <circle cx="50" cy="50" r="40" stroke="rgba(255,255,255,0.1)" strokeWidth="12" fill="none" />
                    <circle cx="50" cy="50" r="40" stroke="#f97316" strokeWidth="12" fill="none" strokeDasharray="251" strokeDashoffset="40" className="animate-pulse" />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-3xl font-light">1,204</span>
                    <span className="text-[10px] text-white/40 uppercase tracking-widest mt-1">Total Users</span>
                  </div>
                 </div>
              </div>
            </motion.div>
          )}

          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-auto hidden sm:block liquid-glass rounded-3xl p-6 relative overflow-hidden group border border-white/10"
          >
            <div className="relative z-10 h-full flex flex-col">
              <div className="mb-8">
                <h2 className="text-4xl font-medium tracking-tighter leading-none mb-4">
                  Innovating the <br />
                  <em className="text-white/60">spirit of learning</em>
                </h2>
                <p className="text-white/40 text-sm leading-relaxed max-w-[240px]">
                  Unlock semantic insights and layered summaries powered by Studymines AI.
                </p>
              </div>

              <div className="mt-auto space-y-3">
                <button 
                  onClick={() => window.open('https://github.com/luciddesigns/edusum', '_blank')}
                  className="w-full liquid-glass py-4 rounded-2xl text-sm font-medium hover:bg-white/5 transition-all text-white/80 border border-white/10 group-hover:border-white/30"
                >
                  Documentation
                </button>
                <button className="w-full bg-white text-black py-4 rounded-2xl text-sm font-semibold hover:bg-white/90 transition-all flex items-center justify-center gap-2 text-balance">
                  <Sparkles size={16} />
                  Go Premium
                </button>
              </div>
            </div>

            {/* DECORATIVE GRADIENT */}
            <div className="absolute -bottom-24 -right-24 h-64 w-64 bg-white/10 rounded-full blur-[80px] pointer-events-none group-hover:bg-white/20 transition-all duration-1000" />
          </motion.div>
        </div>
      </div>

      {/* GLOBAL COGNITIVE CONSULTANT (CHABOT) */}
      <Chatbot user={user} uploadId={selectedUploadId} />
    </div>
  )
}

export default App
