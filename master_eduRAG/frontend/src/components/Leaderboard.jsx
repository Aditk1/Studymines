import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import { 
  Trophy, 
  Users, 
  TrendingUp,
  Search,
  Filter
} from 'lucide-react'

export default function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const response = await axios.get('/api/v1/leaderboard')
        const data = Array.isArray(response.data) ? response.data : response.data.leaderboard || []
        setLeaderboard(data)
        setError(null)
      } catch (err) {
        setError('Ecosystem sync failed. Using local cache.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchLeaderboard()
  }, [])

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-2 border-white/10 border-t-white/80 rounded-full animate-spin" />
        <p className="text-white/40 text-sm font-medium tracking-widest uppercase">Connecting to Ecosystem</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto py-4 space-y-10">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h2 className="text-5xl font-medium tracking-tighter mb-2">Ecosystem <br/><em className="text-white/60">Rankings</em></h2>
          <p className="text-white/40 text-lg">Top contributors and high-retention minds.</p>
        </div>
        
        <div className="flex gap-3">
          <div className="relative">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" />
            <input 
              type="text" 
              placeholder="Filter scholars..." 
              className="liquid-glass pl-10 pr-6 py-3 rounded-2xl text-xs font-medium border border-white/5 focus:outline-none focus:border-white/20 transition-all placeholder:text-white/20"
            />
          </div>
          <button className="liquid-glass px-5 py-3 rounded-2xl text-white/40 hover:text-white transition-colors">
            <Filter size={18} />
          </button>
        </div>
      </header>

      {/* TOP THREE PODIUM (Simulation) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {leaderboard.slice(0, 3).map((user, idx) => (
          <motion.div
            key={user.user_id || idx}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: idx * 0.1 }}
            className={`
              relative p-8 rounded-[2.5rem] text-center flex flex-col items-center
              ${idx === 0 ? 'liquid-glass-strong border border-white/20 ring-1 ring-white/10' : 'liquid-glass'}
            `}
          >
            {idx === 0 && (
              <div className="absolute -top-4 bg-white text-black px-4 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase shadow-xl">
                Zenith Mind
              </div>
            )}
            
            <div className="relative mb-6">
              <div className="w-20 h-20 rounded-full border-2 border-white/10 p-1">
                <img 
                  src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.name}`} 
                  alt={user.name} 
                  className="w-full h-full rounded-full"
                />
              </div>
              <div className={`
                absolute -bottom-2 -right-2 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 border-black
                ${idx === 0 ? 'bg-white text-black' : idx === 1 ? 'bg-white/40 text-white' : 'bg-white/10 text-white/60'}
              `}>
                {idx + 1}
              </div>
            </div>

            <h3 className="text-xl font-medium tracking-tight mb-1">{user.name || `Scholar ${user.user_id}`}</h3>
            <p className="text-white/40 text-xs tracking-widest uppercase mb-4">{user.uploads_count || 0} Artifacts</p>
            
            <div className="w-full h-px bg-white/5 mb-4" />
            
            <div className="text-3xl font-bold tracking-tighter">
              {(user.score || 0).toFixed(1)}<em> pts</em>
            </div>
          </motion.div>
        ))}
      </div>

      {/* LIST TABLE */}
      <div className="liquid-glass rounded-[2.5rem] overflow-hidden border border-white/5">
        <div className="px-8 py-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
          <span className="text-xs font-bold tracking-[0.2em] uppercase text-white/30">Archive Standings</span>
          <Users size={16} className="text-white/20" />
        </div>
        
        <div className="divide-y divide-white/5">
          {leaderboard.length > 0 ? (
            leaderboard.map((user, idx) => (
              <div 
                key={user.user_id || idx} 
                className="group px-8 py-6 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
              >
                <div className="flex items-center gap-6">
                  <span className="text-lg font-medium text-white/20 w-8 group-hover:text-white/40 transition-colors">
                    {idx + 1 < 10 ? `0${idx + 1}` : idx + 1}
                  </span>
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-white/5 border border-white/10 overflow-hidden">
                      <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.name}`} alt="" />
                    </div>
                    <div>
                      <h4 className="font-medium group-hover:text-white transition-colors">{user.name || `Resident ${user.user_id}`}</h4>
                      <div className="flex items-center gap-2 mt-0.5">
                        <TrendingUp size={12} className="text-white/30" />
                        <span className="text-[10px] text-white/20 uppercase tracking-widest font-bold">Consistent Growth</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-12">
                  <div className="hidden sm:block text-right">
                    <div className="text-xs text-white/40 uppercase tracking-widest font-bold mb-0.5">Artifacts</div>
                    <div className="text-sm font-medium">{user.uploads_count || 0}</div>
                  </div>
                  <div className="text-right min-w-[80px]">
                    <div className="text-xs text-white/40 uppercase tracking-widest font-bold mb-0.5">Retention</div>
                    <div className="text-xl font-bold text-white group-hover:scale-110 transition-transform origin-right">
                      {(user.score || 0).toFixed(1)}
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="py-20 text-center text-white/40">
              Initializing Ecosystem Data...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
