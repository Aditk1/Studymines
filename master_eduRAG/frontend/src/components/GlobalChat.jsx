/**
 * Global classroom chat matrix for rooms available to the current user.
 */
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { MessageSquare, Hash, Users } from 'lucide-react'
import axios from 'axios'

/**
 * Global classroom chat matrix for rooms available to the current user.
 */
export default function GlobalChat({ user }) {
  const [chats, setChats] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchChats = async () => {
      try {
        const res = await axios.get('/api/v1/lms/chats/global')
        setChats(res.data)
      } catch (err) {
        console.error("Failed to fetch chats", err)
      } finally {
        setLoading(false)
      }
    }
    fetchChats()
  }, [])

  return (
    <div className="h-full flex flex-col p-2 space-y-6">
      <header className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-3xl font-medium tracking-tighter">Unified <em className="text-white/60">Discussions</em></h2>
          <p className="text-sm text-white/40 mt-1">Global view of all active chatrooms</p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto no-scrollbar pb-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {chats.map((chat, idx) => (
            <motion.div 
              key={chat.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              className="liquid-glass rounded-3xl p-6 group cursor-pointer hover:bg-white/10 transition-all border border-white/5 relative overflow-hidden"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                    <Hash size={18} />
                  </div>
                  <div>
                    <h3 className="font-semibold">{chat.name}</h3>
                    <div className="flex items-center gap-1.5 text-xs text-white/40 mt-0.5">
                      <Users size={12} /> {chat.members} members
                    </div>
                  </div>
                </div>
                <span className="text-[10px] font-medium tracking-wider text-white/30 uppercase">{chat.time}</span>
              </div>
              <div className="bg-white/5 rounded-2xl p-4 border border-white/5 group-hover:bg-white/10 transition-colors">
                <p className="text-sm text-white/70 italic line-clamp-1">"{chat.lastMessage}"</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
