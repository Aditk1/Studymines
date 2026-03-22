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

function App() {
  const [user, setUser] = useState(null)
  const [currentPage, setCurrentPage] = useState('upload')
  const [selectedUploadId, setSelectedUploadId] = useState(null)

  // Auto-login logic (checking localStorage for saved user)
  useEffect(() => {
    const savedUser = localStorage.getItem('studymines_user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
  }, [])

  const handleLogin = (userData) => {
    setUser(userData)
    localStorage.setItem('studymines_user', JSON.stringify(userData))
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('studymines_user')
    setCurrentPage('upload')
  }

  const navItems = [
    { id: 'upload', label: 'Generate', icon: UploadIcon },
    { id: 'dashboard', label: 'Academy', icon: LayoutDashboard },
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
        
        {/* LEFT PANEL: MAIN APP VIEW */}
        <div className="flex-1 flex flex-col h-full min-w-0">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="liquid-glass-strong flex-1 rounded-3xl overflow-hidden flex flex-col p-6 shadow-2xl"
          >
            {/* TOP NAVIGATION BAR */}
            <nav className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <img src="/logo.png" alt="Studymines" className="w-8 h-8 pointer-events-none" />
                <span className="text-2xl font-semibold tracking-tighter lowercase">Study<em>mines</em></span>
              </div>
              
              <div className="hidden md:flex items-center gap-1 bg-white/5 p-1 rounded-full liquid-glass">
                {navItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setCurrentPage(item.id)
                      setSelectedUploadId(null)
                    }}
                    className={`
                      flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-300
                      ${(currentPage === item.id || (currentPage === 'study-lab' && item.id === 'dashboard'))
                        ? 'bg-white/10 text-white shadow-[0_0_15px_rgba(255,255,255,0.1)]' 
                        : 'text-white/40 hover:text-white/70 hover:bg-white/5'}
                    `}
                  >
                    <item.icon size={16} />
                    {item.label}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-4">
                <button className="h-10 w-10 flex items-center justify-center rounded-full bg-white/5 hover:bg-white/10 transition-colors liquid-glass text-white/40 hover:text-white">
                  <Bell size={18} />
                </button>
                <button 
                  onClick={() => setCurrentPage('profile')}
                  className={`flex items-center gap-3 pl-2 pr-4 py-1 rounded-full border transition-all ${
                    currentPage === 'profile' ? 'bg-white/10 border-white/20' : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }`}
                >
                  <div className="h-8 w-8 overflow-hidden rounded-full liquid-glass border border-white/10">
                    <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.email}`} alt="User" />
                  </div>
                  <span className="text-xs font-semibold text-white/60">{user.name.split(' ')[0]}</span>
                </button>
              </div>
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
                  {currentPage === 'leaderboard' && <Leaderboard />}
                  {currentPage === 'research' && <Research />}
                  {currentPage === 'profile' && <Profile user={user} onLogout={handleLogout} />}
                  {currentPage === 'study-lab' && (
                    <StudyLab 
                      uploadId={selectedUploadId} 
                      userId={user.id} 
                      onBack={() => setCurrentPage('dashboard')} 
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

          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="liquid-glass-strong flex-1 rounded-3xl p-6 relative flex flex-col group overflow-hidden"
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
