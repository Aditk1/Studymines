import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Users, MoreVertical, Ban, ShieldCheck, Trash2, XCircle, CheckCircle } from 'lucide-react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

export default function Members({ user: currentUser }) {
  const navigate = useNavigate()
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeMenu, setActiveMenu] = useState(null)
  const [notification, setNotification] = useState(null)
  const [confirmModal, setConfirmModal] = useState(null)

  const notify = (msg, type = 'success') => {
    setNotification({ msg, type })
    setTimeout(() => setNotification(null), 3000)
  }

  const fetchMembers = async () => {
    try {
      const res = await axios.get('/api/v1/lms/members')
      setMembers(res.data)
    } catch (err) {
      console.error("Failed to fetch members", err)
      notify("Failed to load members", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMembers()
  }, [])

  const handleStatusChange = async (memberId, newStatus) => {
    try {
      await axios.post(`/api/v1/lms/members/${memberId}/status`, null, { 
        params: { status: newStatus }
      })
      notify(`Member status updated to ${newStatus}`)
      fetchMembers()
      setActiveMenu(null)
    } catch (err) {
      notify("Failed to update status", "error")
    }
  }

  const handleRoleChange = async (memberId, currentRole) => {
    const nextRole = currentRole === 'student' ? 'teacher' : 'student'
    setConfirmModal({
      title: "Update Role?",
      message: `Change user role to ${nextRole.toUpperCase()}? This will grant them ${nextRole === 'teacher' ? 'academic control' : 'student-level access'}.`,
      confirmText: "Change Role",
      onConfirm: async () => {
        try {
          await axios.post(`/api/v1/lms/members/${memberId}/role`, null, { 
            params: { role: nextRole }
          })
          notify(`Member role changed to ${nextRole}`)
          fetchMembers()
          setActiveMenu(null)
          setConfirmModal(null)
        } catch (err) {
          notify("Failed to update role", "error")
          setConfirmModal(null)
        }
      }
    })
  }

  const handleViewMastery = (memberId) => {
    navigate(`/analytics?user_id=${memberId}`)
    setActiveMenu(null)
  }

  const handleDelete = async (memberId) => {
    setConfirmModal({
      title: "Confirm Deletion",
      message: "Are you sure you want to PERMANENTLY delete this user? All their records, including mastery data and course enrollments, will be erased. This cannot be undone.",
      confirmText: "Delete Permanently",
      variant: "danger",
      onConfirm: async () => {
        try {
          await axios.delete(`/api/v1/lms/members/${memberId}`)
          notify("Member deleted permanently")
          setMembers(prev => prev.filter(m => m.id !== memberId))
          setActiveMenu(null)
          setConfirmModal(null)
        } catch (err) {
          notify("Deletion failed. Insufficient permissions or student has active records.", "error")
          setConfirmModal(null)
        }
      }
    })
  }


  return (
    <div className="h-full flex flex-col p-2 space-y-6">
      <header className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-3xl font-medium tracking-tighter">Tenant <em className="text-white/60">Members</em></h2>
          <p className="text-sm text-white/40 mt-1">Manage global access and roles</p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto no-scrollbar pb-10 relative">
        <div className="bg-white/[0.02] border border-white/5 rounded-3xl liquid-glass relative">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 uppercase tracking-widest text-[10px] text-white/30 bg-white/5 rounded-t-3xl">
                <th className="p-5 font-bold rounded-tl-3xl">User</th>
                <th className="p-5 font-bold">Role</th>
                <th className="p-5 font-bold">Status</th>
                <th className="p-5 font-bold text-right rounded-tr-3xl">Actions</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member, idx) => (
                <motion.tr 
                  key={member.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="border-b border-white/5 hover:bg-white/[0.05] transition-colors group relative"
                >
                  <td className="p-5">
                    <div className="flex items-center gap-4">
                      <div className="relative">
                        <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${member.email}`} className="w-10 h-10 rounded-full border border-white/10" alt={member.name} />
                        {member.status === 'active' && <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-[#121212] rounded-full shadow-lg"></div>}
                        {member.status === 'banned' && <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-red-500 border-2 border-[#121212] rounded-full shadow-lg"></div>}
                      </div>
                      <div>
                        <div className="font-semibold text-white/90">{member.name}</div>
                        <div className="text-[11px] text-white/30 font-mono">{member.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-5">
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${member.role === 'teacher' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-white/5 text-white/40 border border-white/5'}`}>
                      {member.role}
                    </span>
                  </td>
                  <td className="p-5">
                    <div className={`flex items-center gap-2 text-xs font-semibold ${member.status === 'banned' ? 'text-red-400' : 'text-green-400'}`}>
                      <div className={`w-1.5 h-1.5 rounded-full ${member.status === 'banned' ? 'bg-red-400 shadow-[0_0_8px_#f87171]' : 'bg-green-400 shadow-[0_0_8px_#4ade80]'}`}></div>
                      <span className="capitalize">{member.status}</span>
                    </div>
                  </td>
                  <td className={`p-5 text-right relative ${activeMenu === member.id ? 'z-[1100]' : 'z-10'}`}>
                    <div className="flex items-center justify-end gap-1">
                      {member.status === 'active' ? (
                        <button 
                          onClick={(e) => {
                            e.stopPropagation()
                            handleStatusChange(member.id, 'banned')
                          }}
                          className="h-8 w-8 rounded-full flex items-center justify-center text-white/20 hover:text-red-400 hover:bg-red-500/10 transition-all" 
                          title="Restrict Access"
                        >
                          <Ban size={14} />
                        </button>
                      ) : (
                        <button 
                          onClick={(e) => {
                            e.stopPropagation()
                            handleStatusChange(member.id, 'active')
                          }}
                          className="h-8 w-8 rounded-full flex items-center justify-center text-white/20 hover:text-green-400 hover:bg-green-500/10 transition-all" 
                          title="Restore Access"
                        >
                          <CheckCircle size={14} />
                        </button>
                      )}

                      <div className="relative">
                        <button 
                          onClick={(e) => {
                            e.stopPropagation()
                            setActiveMenu(activeMenu === member.id ? null : member.id)
                          }}
                          className={`h-8 w-8 rounded-full flex items-center justify-center transition-all ${activeMenu === member.id ? 'bg-white/20 text-white' : 'text-white/20 hover:text-white hover:bg-white/10 shadow-sm'}`}
                        >
                          <MoreVertical size={16} />
                        </button>
                        
                        <AnimatePresence>
                          {activeMenu === member.id && (
                            <>
                              {/* Transparent invisible click-outside layer dedicated to this dropdown */}
                              <div 
                                className="fixed inset-0 z-40 cursor-default" 
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setActiveMenu(null)
                                }}
                              />
                              <motion.div 
                                initial={{ opacity: 0, scale: 0.95, y: idx > (members.length - 3) ? 10 : -10 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: idx > (members.length - 3) ? 10 : -10 }}
                                className={`absolute right-0 ${idx > (members.length - 3) ? 'bottom-full mb-2' : 'top-full mt-2'} w-52 bg-[#121212] border border-white/10 rounded-2xl shadow-[0_30px_60px_rgba(0,0,0,0.9)] z-50 overflow-hidden backdrop-blur-3xl`}
                                onClick={(e) => e.stopPropagation()}
                              >
                                <div className="p-2">
                                  <div className="px-3 py-2 text-[9px] font-bold text-white/20 uppercase tracking-widest leading-none mb-1">Management</div>
                                  <button 
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      handleViewMastery(member.id)
                                    }}
                                    className="w-full flex items-center gap-3 px-3 py-3 text-xs text-white/60 hover:text-white hover:bg-white/5 rounded-xl transition-all group/item text-left"
                                  >
                                    <Users size={14} className="group-hover/item:text-indigo-400" /> 
                                    <span>Knowledge Map</span>
                                  </button>
                                  
                                  {/* Role change restricted to Admin */}
                                  {currentUser?.role === 'admin' && (
                                    <button 
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        handleRoleChange(member.id, member.role)
                                      }}
                                      className="w-full flex items-center gap-3 px-3 py-3 text-xs text-white/60 hover:text-white hover:bg-white/5 rounded-xl transition-all group/item text-left"
                                    >
                                      <ShieldCheck size={14} className="group-hover/item:text-blue-400" />
                                      <span>Swap Role</span>
                                    </button>
                                  )}
                                  
                                  <div className="h-px bg-white/5 my-1.5 mx-2" />
                                  
                                  {/* Delete restricted: Teacher can only delete students. Admins can delete anyone. */}
                                  {(currentUser?.role === 'admin' || (currentUser?.role === 'teacher' && member.role === 'student')) && (
                                    <button 
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        handleDelete(member.id)
                                      }}
                                      className="w-full flex items-center gap-3 px-3 py-3 text-xs text-red-100/50 hover:text-red-400 hover:bg-red-600/20 rounded-xl transition-all group/item text-left"
                                    >
                                      <Trash2 size={14} /> 
                                      <span>Unenroll {member.role}</span>
                                    </button>
                                  )}
                                  
                                  {/* If no administrative actions are allowed for this user view */}
                                  {currentUser?.role === 'teacher' && member.role !== 'student' && (
                                    <div className="px-3 py-2 text-[10px] italic text-white/20 leading-tight">
                                      Higher-tier permissions required to manage instructors.
                                    </div>
                                  )}
                                </div>
                              </motion.div>
                            </>
                          )}
                        </AnimatePresence>
                      </div>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Inline notification */}
      <AnimatePresence>
        {notification && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className={`fixed bottom-6 right-6 z-[200] px-5 py-3 rounded-2xl text-sm font-medium shadow-2xl backdrop-blur-xl border ${notification.type === 'error' ? 'bg-red-500/20 border-red-500/30 text-red-300' : 'bg-green-500/20 border-green-500/30 text-green-300'}`}
          >
            {notification.msg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Custom Confirmation Modal */}
      <AnimatePresence>
        {confirmModal && (
          <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setConfirmModal(null)}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="relative w-full max-w-sm bg-[#1a1a1a] border border-white/10 rounded-[2rem] p-8 shadow-[0_50px_100px_rgba(0,0,0,0.8)] overflow-hidden"
            >
              <div className="absolute top-0 right-0 p-8 w-32 h-32 bg-indigo-500/10 blur-[80px] rounded-full pointer-events-none" />
              
              <h3 className="text-2xl font-semibold mb-3 tracking-tight">{confirmModal.title}</h3>
              <p className="text-white/40 text-sm leading-relaxed mb-8">
                {confirmModal.message}
              </p>
              
              <div className="flex flex-col gap-3">
                <button 
                  onClick={confirmModal.onConfirm}
                  className={`w-full py-4 rounded-2xl font-bold uppercase tracking-widest text-[10px] transition-all
                    ${confirmModal.variant === 'danger' 
                      ? 'bg-red-500 hover:bg-red-600 shadow-[0_10px_20px_rgba(239,68,68,0.3)] text-white' 
                      : 'bg-white text-black hover:bg-indigo-500 hover:text-white'
                    }
                  `}
                >
                  {confirmModal.confirmText || 'Confirm'}
                </button>
                <button 
                  onClick={() => setConfirmModal(null)}
                  className="w-full py-4 rounded-2xl font-bold uppercase tracking-widest text-[10px] text-white/40 hover:text-white hover:bg-white/5 transition-all"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}



