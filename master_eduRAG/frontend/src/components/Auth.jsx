/**
 * Authentication screen for login and signup against the FastAPI auth endpoints.
 */
import { useState } from 'react'
import axios from 'axios'
import { supabase } from '../supabase'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Sparkles, 
  Mail, 
  Lock, 
  User as UserIcon, 
  ArrowRight,
  ChevronRight,
  ShieldCheck,
  Cpu
} from 'lucide-react'

/**
 * Authentication screen for login and signup against the FastAPI auth endpoints.
 */
export default function Auth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    student_level: 'undergraduate',
    role: 'student'
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    try {
      if (isLogin) {
        // --- API-BASED LOGIN (Supports Auto-Detect) ---
        const payload = new FormData()
        payload.append('email', formData.email)
        payload.append('password', formData.password)

        const { data } = await axios.post('/api/v1/auth/login', payload)
        
        if (data.success) {
          onLogin(data.user, data.access_token)
        } else {
          throw new Error(data.error || 'Identity verify failure')
        }
      } else {
        // --- API-BASED SIGNUP (Supports Explicit Role Choice) ---
        const payload = new FormData()
        payload.append('name', formData.name)
        payload.append('email', formData.email)
        payload.append('password', formData.password)
        payload.append('student_level', formData.student_level)
        payload.append('role', formData.role)

        const { data } = await axios.post('/api/v1/auth/signup', payload)
        
        if (data.success) {
          onLogin(data.user, data.access_token)
        } else {
          throw new Error(data.error || 'Archive initialization failed')
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Archive connection failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-xl p-6">
      
      {/* DECORATIVE ELEMENTS */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-white/[0.03] rounded-full blur-[120px] pointer-events-none" />
      
      <motion.div 
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="w-full max-w-md liquid-glass-strong rounded-[3rem] p-10 relative overflow-hidden shadow-2xl"
      >
        <div className="relative z-10">
          <header className="text-center mb-6">
            <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mx-auto mb-6 liquid-glass">
              <Sparkles size={32} className="text-white/60" />
            </div>
            <h1 className="text-4xl font-medium tracking-tighter mb-2 text-balance">
              {isLogin ? 'Synchronize ' : 'Initialize '}
              <em className="text-white/60">Archive</em>
            </h1>
            <p className="text-white/40 text-sm">Adaptive Cognitive Learning System</p>
          </header>

          <form onSubmit={handleSubmit} className="space-y-4">
            <AnimatePresence mode="wait">
              {!isLogin && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-4 overflow-visible"
                >
                  <div className="relative">
                    <UserIcon size={18} className="absolute left-5 top-1/2 -translate-y-1/2 text-white/20" />
                    <input
                      type="text"
                      placeholder="Scholar Name"
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      className="w-full bg-white/5 border border-white/5 rounded-2xl py-4 pl-14 pr-6 text-sm focus:bg-white/10 transition-all outline-none"
                    />
                  </div>

                  {/* ROLE SELECTION */}
                  <div className="flex gap-2 p-1.5 bg-white/5 rounded-2xl border border-white/5">
                    {['student', 'teacher'].map(role => (
                      <button
                        key={role}
                        type="button"
                        onClick={() => setFormData({...formData, role: role})}
                        className={`flex-1 py-3 rounded-xl text-xs font-bold uppercase tracking-widest transition-all ${
                          formData.role === role 
                          ? 'bg-white/10 text-white shadow-lg' 
                          : 'text-white/20 hover:text-white/40'
                        }`}
                      >
                        {role}
                      </button>
                    ))}
                  </div>
                  
                  {formData.role === 'student' && (
                    <div className="grid grid-cols-3 gap-2">
                      {['high_school', 'undergraduate', 'postgraduate'].map(level => (
                        <button
                          key={level}
                          type="button"
                          onClick={() => setFormData({...formData, student_level: level})}
                          className={`py-2 rounded-xl text-[9px] font-bold uppercase tracking-widest border transition-all ${
                            formData.student_level === level 
                            ? 'bg-white/10 border-white/20 text-white' 
                            : 'bg-transparent border-white/5 text-white/20 hover:border-white/10'
                          }`}
                        >
                          {level.replace('_', ' ')}
                        </button>
                      ))}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            <div className="relative">
              <Mail size={18} className="absolute left-5 top-1/2 -translate-y-1/2 text-white/20" />
              <input
                type="email"
                placeholder="Institutional Email"
                required
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full bg-white/5 border border-white/5 rounded-2xl py-4 pl-14 pr-6 text-sm focus:bg-white/10 transition-all outline-none underline-offset-4"
              />
            </div>

            <div className="relative">
              <Lock size={18} className="absolute left-5 top-1/2 -translate-y-1/2 text-white/20" />
              <input
                type="password"
                placeholder="Archive Passcode"
                required
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="w-full bg-white/5 border border-white/5 rounded-2xl py-4 pl-14 pr-6 text-sm focus:bg-white/10 transition-all outline-none"
              />
            </div>

            {error && (
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-400 text-xs text-center font-medium">
                {error}
              </motion.p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-white text-black py-4 rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-white/90 active:scale-95 transition-all mt-6 shadow-xl shadow-white/5"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-black/20 border-t-black rounded-full animate-spin" />
              ) : (
                <>
                  {isLogin ? 'Access Archive' : 'Create Credentials'}
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <footer className="mt-8 text-center">
            <button 
              onClick={() => setIsLogin(!isLogin)}
              className="text-white/40 text-xs hover:text-white transition-colors"
            >
              {isLogin ? (
                <span>No credentials? <em className="text-white/80 not-italic font-bold">Join the Academy</em></span>
              ) : (
                <span>Already a scholar? <em className="text-white/80 not-italic font-bold">Access Archive</em></span>
              )}
            </button>
          </footer>
          
          <div className="mt-12 pt-8 border-t border-white/5 flex items-center justify-between opacity-30 grayscale pointer-events-none">
             <div className="flex items-center gap-2">
                <ShieldCheck size={14} />
                <span className="text-[10px] font-bold tracking-[0.2em] uppercase">AES-256</span>
             </div>
             <div className="flex items-center gap-2">
                <Cpu size={14} />
                <span className="text-[10px] font-bold tracking-[0.2em] uppercase">Studymines AI</span>
             </div>
          </div>
        </div>
        
        {/* INTERIOR LIGHTING */}
        <div className="absolute -bottom-20 -right-20 w-64 h-64 bg-white/5 rounded-full blur-3xl pointer-events-none" />
      </motion.div>
    </div>
  )
}
