import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Users, BookOpen, Settings, Hash, Search, ArrowRight } from 'lucide-react'
import axios from 'axios'
import ClassroomDetail from './ClassroomDetail'

const ChevronRight = ({ size, className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="m9 18 6-6-6-6"/></svg>
)

export default function Classrooms({ user, onOpenArtifact }) {
  const [classrooms, setClassrooms] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showJoinModal, setShowJoinModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedClassroomId, setSelectedClassroomId] = useState(null)

  useEffect(() => {
    const fetchClassrooms = async () => {
      try {
        const response = await axios.get('/api/v1/lms/classrooms')
        setClassrooms(response.data)
      } catch (err) {
        console.error("Failed to fetch classrooms", err)
      } finally {
        setLoading(false)
      }
    }
    fetchClassrooms()
  }, [])

  if (selectedClassroomId) {
    return (
      <ClassroomDetail 
        classroomId={selectedClassroomId}
        user={user}
        onBack={() => setSelectedClassroomId(null)}
        onOpenArtifact={onOpenArtifact}
      />
    )
  }

  return (
    <div className="h-full flex flex-col p-2 space-y-6">
      
      <header className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-3xl font-medium tracking-tighter">My <em className="text-white/60">Classes</em></h2>
          <p className="text-sm text-white/40 mt-1">Manage physical & cognitive batches</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" size={16} />
            <input 
              type="text" 
              placeholder="Search classes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-white/5 border border-white/5 rounded-full py-2.5 pl-10 pr-4 text-sm focus:bg-white/10 transition-all outline-none w-64"
            />
          </div>
          {user?.role === 'teacher' ? (
            <button 
              onClick={() => setShowCreateModal(true)}
              className="bg-white text-black pl-4 pr-5 py-2.5 rounded-full text-sm font-semibold flex items-center gap-2 hover:bg-white/90 transition-all shadow-[0_0_20px_rgba(255,255,255,0.2)]"
            >
              <Plus size={18} />
              Create Class
            </button>
          ) : (
            <button 
              onClick={() => setShowJoinModal(true)}
              className="liquid-glass border border-white/10 pl-4 pr-5 py-2.5 rounded-full text-sm font-semibold flex items-center gap-2 hover:bg-white/10 transition-all"
            >
              <ArrowRight size={18} />
              Join Class
            </button>
          )}
        </div>
      </header>

      {/* CLASSROOM GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full h-40 flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          </div>
        ) : (
          classrooms.filter(c => c.name.toLowerCase().includes(searchQuery.toLowerCase())).map((classroom, i) => (
            <motion.div
              key={classroom.id}
              onClick={() => setSelectedClassroomId(classroom.id)}
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="liquid-glass rounded-[2rem] p-6 group cursor-pointer hover:bg-white/5 transition-all relative overflow-hidden flex flex-col h-64 border border-white/5 hover:border-white/20"
            >
              {/* Abstract decorative background */}
              <div className="absolute -top-10 -right-10 w-40 h-40 bg-white/5 rounded-full blur-3xl pointer-events-none group-hover:bg-white/10 transition-all" />

              <div className="flex items-start justify-between mb-4 relative z-10">
                <div className="px-3 py-1 bg-white/[0.03] border border-white/10 rounded-full text-[10px] font-bold tracking-widest uppercase text-white/50 flex items-center gap-1.5 backdrop-blur-md">
                  <Hash size={10} />
                  {classroom.code}
                </div>
                {classroom.is_teacher && (
                  <button className="h-8 w-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-white/10 transition-all text-white/40 hover:text-white">
                    <Settings size={14} />
                  </button>
                )}
              </div>

              <div className="relative z-10 flex-1">
                <h3 className="text-xl font-medium tracking-tight mb-2 leading-tight">{classroom.name}</h3>
                <p className="text-xs font-semibold uppercase tracking-wider text-white/30">{classroom.subject}</p>
              </div>

              <div className="relative z-10 mt-auto flex items-center justify-between border-t border-white/5 pt-4">
                <div className="flex gap-4">
                  <div className="flex items-center gap-1.5 text-white/40 text-xs font-medium">
                    <Users size={14} />
                    {classroom.member_count}
                  </div>
                  <div className="flex items-center gap-1.5 text-white/40 text-xs font-medium">
                    <BookOpen size={14} />
                    {classroom.material_count} docs
                  </div>
                </div>

                <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center text-black opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all shadow-xl">
                  <ChevronRight size={16} />
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>

      {/* CREATE CLASS MODAL */}
      <AnimatePresence>
        {showCreateModal && (
          <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-zinc-900 border border-white/10 p-6 rounded-2xl w-full max-w-md"
            >
              <h3 className="text-xl font-medium mb-4">Create New Classroom</h3>
              <form onSubmit={async (e) => {
                e.preventDefault()
                const formData = new FormData(e.target)
                try {
                  const res = await axios.post('/api/v1/lms/classrooms', {
                    name: formData.get('name'),
                    subject: formData.get('subject'),
                    description: formData.get('description')
                  })
                  setClassrooms([...classrooms, res.data])
                  setShowCreateModal(false)
                } catch (err) {
                  console.error(err)
                }
              }} className="space-y-4">
                <input required name="name" placeholder="Classroom Name" className="w-full bg-white/5 border border-white/10 rounded-xl p-3 outline-none focus:border-white/20" />
                <input required name="subject" placeholder="Subject (e.g., Physics)" className="w-full bg-white/5 border border-white/10 rounded-xl p-3 outline-none focus:border-white/20" />
                <textarea name="description" placeholder="Description" className="w-full bg-white/5 border border-white/10 rounded-xl p-3 outline-none focus:border-white/20 h-24" />
                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 rounded-xl text-white/50 hover:bg-white/5 transition-colors">Cancel</button>
                  <button type="submit" className="px-5 py-2 rounded-xl bg-white text-black font-medium hover:bg-white/90">Create</button>
                </div>
              </form>
            </motion.div>
          </div>
        )}

        {showJoinModal && (
          <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-zinc-900 border border-white/10 p-6 rounded-2xl w-full max-w-md"
            >
              <h3 className="text-xl font-medium mb-4">Join Classroom</h3>
              <form onSubmit={async (e) => {
                e.preventDefault()
                const formData = new FormData(e.target)
                try {
                  const res = await axios.post('/api/v1/lms/classrooms/join', {
                    code: formData.get('code')
                  })
                  if (res.data.success) {
                    alert(res.data.status === 'pending' ? 'Request sent! Waiting for teacher approval.' : 'Joined successfully! Refresh your classes.')
                  }
                  setShowJoinModal(false)
                } catch (err) {
                  alert(err.response?.data?.detail || 'Failed to join class.')
                }
              }} className="space-y-4">
                <input required name="code" placeholder="Enter Classroom Code (e.g. MATH-1A2B3C)" className="w-full bg-white/5 border border-white/10 rounded-xl p-3 outline-none focus:border-white/20" />
                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" onClick={() => setShowJoinModal(false)} className="px-4 py-2 rounded-xl text-white/50 hover:bg-white/5 transition-colors">Cancel</button>
                  <button type="submit" className="px-5 py-2 rounded-xl bg-white text-black font-medium hover:bg-white/90">Request to Join</button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
