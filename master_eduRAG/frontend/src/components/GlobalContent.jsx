import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Plus, Search, Filter, BookOpen, 
  ChevronRight, Brain, Clock, Share2, 
  MoreVertical, FileText, UploadCloud 
} from 'lucide-react'
import axios from 'axios'

export default function GlobalContent({ user, onOpenArtifact }) {
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFilter, setSelectedFilter] = useState('all')

  useEffect(() => {
    const fetchMaterials = async () => {
      try {
        const res = await axios.get('/api/v1/lms/materials/global')
        setMaterials(res.data)
      } catch (err) {
        console.error("Failed to fetch global materials", err)
      } finally {
        setLoading(false)
      }
    }
    fetchMaterials()
  }, [])

  const filteredMaterials = materials.filter(m => {
    const matchesSearch = m.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          m.subject.toLowerCase().includes(searchQuery.toLowerCase())
    if (selectedFilter === 'all') return matchesSearch
    return matchesSearch && m.subject.toLowerCase() === selectedFilter.toLowerCase()
  })

  // Group by subject for the filter pill list
  const subjects = ['all', ...new Set(materials.map(m => m.subject))]

  return (
    <div className="h-full flex flex-col p-2 space-y-10">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 overflow-x-hidden">
        <div>
          <h2 className="text-5xl font-medium tracking-tighter mb-2">Global <em className="text-white/60">Content</em></h2>
          <p className="text-white/30 text-lg">Manage all documents across classrooms</p>
        </div>

        <div className="flex items-center gap-4">
           <div className="relative group">
              <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-white/60 transition-colors" />
              <input 
                type="text" 
                placeholder="Search resources..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-white/5 border border-white/5 rounded-2xl py-3.5 pl-12 pr-6 text-sm focus:bg-white/10 transition-all outline-none w-64 focus:w-80 border-white/0 focus:border-white/10"
              />
           </div>
           <button className="bg-white text-black px-6 py-3.5 rounded-2xl text-xs font-bold uppercase tracking-widest flex items-center gap-2 hover:bg-white/90 transition-all shadow-xl shadow-white/10 active:scale-95">
              <UploadCloud size={16} />
              Upload Resource
           </button>
        </div>
      </header>

      {/* FILTER PILLS */}
      <div className="flex items-center gap-2 flex-wrap pb-2 no-scrollbar">
          {subjects.map(sub => (
            <button 
                key={sub}
                onClick={() => setSelectedFilter(sub)}
                className={`px-5 py-2 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all border
                    ${selectedFilter === sub ? 'bg-white text-black border-white' : 'bg-white/5 text-white/40 border-white/5 hover:bg-white/10'}
                `}
            >
                {sub}
            </button>
          ))}
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-20">
        {loading ? (
             <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {[1,2,3,4,5,6].map(i => (
                    <div key={i} className="h-64 liquid-glass rounded-[2.5rem] animate-pulse border border-white/5" />
                ))}
             </div>
        ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                {filteredMaterials.map((artifact, idx) => (
                    <motion.div
                        key={artifact.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.05 }}
                        onClick={() => onOpenArtifact(artifact.id)}
                        className="liquid-glass rounded-[2.5rem] p-8 flex flex-col min-h-[16rem] group cursor-pointer hover:bg-white/[0.04] border border-white/5 hover:border-white/20 transition-all relative overflow-hidden"
                    >
                        {/* Background flourish */}
                        <div className="absolute -top-10 -right-10 w-32 h-32 bg-white/[0.02] rounded-full blur-3xl group-hover:bg-white/[0.05] transition-colors" />

                        <div className="flex items-start justify-between mb-6 relative z-10">
                            <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10 group-hover:bg-indigo-500/20 group-hover:text-indigo-400 transition-all">
                                <FileText size={24} />
                            </div>
                            <div className="flex items-center gap-3 opacity-20 group-hover:opacity-100 transition-opacity">
                                <Share2 size={16} className="hover:text-indigo-400" />
                                <MoreVertical size={16} />
                            </div>
                        </div>

                        <div className="flex-1 relative z-10">
                            <h3 className="text-xl font-medium tracking-tight mb-2 group-hover:text-white transition-colors">{artifact.title}</h3>
                            <div className="flex items-center gap-3 text-[10px] font-bold tracking-[0.2em] uppercase text-white/20 group-hover:text-white/40 transition-colors">
                                <span>{artifact.subject}</span>
                                <span className="w-1 h-1 rounded-full bg-white/20" />
                                <span>{artifact.classroom_name}</span>
                            </div>
                            <p className="text-xs text-white/30 hidden md:block mt-4 line-clamp-2 italic leading-relaxed">
                                "{artifact.summary}"
                            </p>
                        </div>

                        <div className="mt-8 pt-6 border-t border-white/5 flex items-center justify-between relative z-10 transition-all">
                            <div className="flex gap-4">
                                <div className="flex items-center gap-1.5 text-white/40 group-hover:text-white/60 transition-colors">
                                    <Brain size={14} />
                                    <span className="text-[10px] font-bold">{artifact.concept_count} Nodes</span>
                                </div>
                                <div className="flex items-center gap-1.5 text-white/40 group-hover:text-white/60 transition-colors">
                                    <Clock size={14} />
                                    <span className="text-[10px] font-bold capitalize">{artifact.status}</span>
                                </div>
                            </div>
                            <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center text-black opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all shadow-xl shadow-white/5">
                                <ChevronRight size={16} />
                            </div>
                        </div>
                    </motion.div>
                ))}
                {filteredMaterials.length === 0 && (
                    <div className="col-span-full py-40 text-center space-y-4">
                         <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto text-white/10">
                            <BookOpen size={32} />
                         </div>
                         <h4 className="text-xl font-medium text-white/30 tracking-tight">Ecosystem Archive is empty</h4>
                         <p className="text-white/10 text-sm">Upload documents to populate the Global Content Matrix.</p>
                    </div>
                )}
            </div>
        )}
      </div>
    </div>
  )
}
