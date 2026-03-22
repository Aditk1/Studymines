import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Users, MoreVertical, Ban, ShieldCheck } from 'lucide-react'
import axios from 'axios'

export default function Members({ user }) {
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMembers = async () => {
      try {
        const res = await axios.get('/api/v1/lms/members')
        setMembers(res.data)
      } catch (err) {
        console.error("Failed to fetch members", err)
      } finally {
        setLoading(false)
      }
    }
    fetchMembers()
  }, [])

  return (
    <div className="h-full flex flex-col p-2 space-y-6">
      <header className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-3xl font-medium tracking-tighter">Tenant <em className="text-white/60">Members</em></h2>
          <p className="text-sm text-white/40 mt-1">Manage global access and roles</p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto no-scrollbar pb-10">
        <div className="bg-white/[0.02] border border-white/5 rounded-3xl overflow-hidden liquid-glass">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 uppercase tracking-widest text-[10px] text-white/30 bg-white/5">
                <th className="p-5 font-bold">User</th>
                <th className="p-5 font-bold">Role</th>
                <th className="p-5 font-bold">Status</th>
                <th className="p-5 font-bold text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member, idx) => (
                <motion.tr 
                  key={member.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="border-b border-white/5 hover:bg-white/[0.05] transition-colors"
                >
                  <td className="p-5">
                    <div className="flex items-center gap-4">
                      <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${member.email}`} className="w-10 h-10 rounded-full border border-white/10" alt={member.name} />
                      <div>
                        <div className="font-semibold">{member.name}</div>
                        <div className="text-xs text-white/40">{member.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-5">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${member.role === 'teacher' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-white/10 text-white/60 border border-white/5'}`}>
                      {member.role}
                    </span>
                  </td>
                  <td className="p-5">
                    <div className="flex items-center gap-2 text-xs font-medium text-green-400">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-400 shadow-[0_0_10px_#4ade80]"></div>
                      {member.status}
                    </div>
                  </td>
                  <td className="p-5 text-right flex items-center justify-end gap-2">
                    {member.role === 'student' && (
                      <button className="h-8 w-8 rounded-full flex items-center justify-center text-white/20 hover:text-white hover:bg-white/10 transition-colors" title="Revoke Access">
                        <Ban size={14} />
                      </button>
                    )}
                    <button className="h-8 w-8 rounded-full flex items-center justify-center text-white/20 hover:text-white hover:bg-white/10 transition-colors">
                      <MoreVertical size={16} />
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
