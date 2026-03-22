import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { BookOpen, FileText, Search, Filter, MoreVertical, UploadCloud } from 'lucide-react'
import axios from 'axios'

export default function Content({ user, onOpenArtifact }) {
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMaterials = async () => {
      try {
        const res = await axios.get('/api/v1/lms/materials/global')
        setMaterials(res.data)
      } catch (err) {
        console.error("Failed to fetch materials", err)
      } finally {
        setLoading(false)
      }
    }
    fetchMaterials()
  }, [])

  return (
    <div className="h-full flex flex-col p-2 space-y-6">
      <header className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-3xl font-medium tracking-tighter">Global <em className="text-white/60">Content</em></h2>
          <p className="text-sm text-white/40 mt-1">Manage all documents across classrooms</p>
        </div>
        <div className="flex gap-4">
          <button className="bg-white text-black pl-4 pr-5 py-2.5 rounded-full text-sm font-semibold flex items-center gap-2 hover:bg-white/90 transition-all">
            <UploadCloud size={18} /> Upload Resource
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto no-scrollbar pb-10">
        <div className="grid grid-cols-1 gap-4">
          {materials.map((item, idx) => (
            <motion.div 
              key={item.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              onClick={() => onOpenArtifact(item.id)}
              className="liquid-glass rounded-2xl p-5 flex items-center justify-between cursor-pointer hover:bg-white/10 transition-colors border border-white/5"
            >
              <div className="flex items-center gap-5">
                <div className="w-12 h-12 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
                  <FileText size={20} />
                </div>
                <div>
                  <h4 className="font-semibold tracking-tight text-white">{item.title}</h4>
                  <div className="flex items-center gap-3 mt-1 text-xs text-white/40 font-medium tracking-wide border-l border-white/10 pl-2">
                    <span className="text-orange-300/80">{item.class}</span>
                    <span>•</span>
                    <span>Uploaded {item.date}</span>
                    <span>•</span>
                    <span>{item.uses} Extractions</span>
                  </div>
                </div>
              </div>
              <button className="h-8 w-8 rounded-full flex items-center justify-center text-white/20 hover:text-white hover:bg-white/10 transition-colors">
                <MoreVertical size={16} />
              </button>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
