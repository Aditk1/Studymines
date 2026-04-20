import { useState, useRef } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FileText, 
  Image as ImageIcon, 
  Upload as UploadIcon, 
  CheckCircle2, 
  AlertCircle,
  X,
  Plus,
  ArrowRight,
  BookOpen,
  HelpCircle,
  Library
} from 'lucide-react'

export default function Upload({ userId, onOpenArtifact }) {
  const [uploadType, setUploadType] = useState('document')
  const [file, setFile] = useState(null)
  const [subject, setSubject] = useState('')
  const [topic, setTopic] = useState('')
  const [studentLevel, setStudentLevel] = useState('undergraduate')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a file to continue')
      return
    }

    setLoading(true)
    setError(null)
    
    const formData = new FormData()
    formData.append('file', file)
    formData.append('user_id', userId)
    formData.append('analyze', 'true')
    if (subject) formData.append('subject', subject)
    if (topic) formData.append('topic', topic)
    formData.append('student_level', studentLevel)

    try {
      const endpoint = uploadType === 'document' 
        ? '/api/v1/upload/document'
        : '/api/v1/upload/image'
      
      const response = await axios.post(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      setResult(response.data)
      setFile(null)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Processing failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-4">
      <header className="mb-10">
        <h2 className="text-5xl font-medium tracking-tighter mb-2">Generate <em className="text-white/60">Insight</em></h2>
        <p className="text-white/40 text-lg">Upload material to create your semantic study package.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* FORM PANEL */}
        <div className="lg:col-span-7 space-y-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* TYPE SELECTION */}
            <div className="flex p-1 bg-white/5 rounded-2xl liquid-glass w-fit">
              {['document', 'image'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => {
                    setUploadType(type)
                    setFile(null)
                    if (fileInputRef.current) fileInputRef.current.value = ""
                  }}
                  className={`
                    flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 capitalize
                    ${uploadType === type ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white/60'}
                  `}
                >
                  {type === 'document' ? <FileText size={16} /> : <ImageIcon size={16} />}
                  {type}
                </button>
              ))}
            </div>

            {/* DROPZONE */}
            <div 
              onClick={() => fileInputRef.current.click()}
              className={`
                group relative border-2 border-dashed rounded-[2rem] p-12 transition-all cursor-pointer overflow-hidden
                ${file ? 'border-white/40 bg-white/5' : 'border-white/10 hover:border-white/30 hover:bg-white/5'}
              `}
            >
              <input 
                type="file" 
                ref={fileInputRef}
                onChange={handleFileChange} 
                className="hidden" 
                accept={uploadType === 'document' ? ".pdf,.docx,.pptx,.txt" : "image/*"}
              />
              
              <div className="relative z-10 flex flex-col items-center text-center">
                <div className={`
                  w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-all duration-500
                  ${file ? 'bg-white/20 text-white shadow-[0_0_30px_rgba(255,255,255,0.1)]' : 'bg-white/5 text-white/40 group-hover:bg-white/10 group-hover:text-white/60'}
                `}>
                  {file ? <CheckCircle2 size={32} /> : <UploadIcon size={32} />}
                </div>
                
                {file ? (
                  <div>
                    <p className="text-lg font-medium truncate max-w-xs">{file.name}</p>
                    <p className="text-sm text-white/40">{(file.size / (1024 * 1024)).toFixed(2)} MB • Ready to bloom</p>
                  </div>
                ) : (
                  <div>
                    <p className="text-lg font-medium">Click or drag a {uploadType}</p>
                    <p className="text-sm text-white/40 mt-1">
                      {uploadType === 'document' 
                        ? 'PDF, PPTX, DOCX, TXT up to 50MB' 
                        : 'JPG, PNG, WEBP, HEIC up to 10MB'}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* METADATA FIELDS */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold tracking-widest uppercase text-white/30 ml-1">Subject</label>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g., Biology"
                  className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-sm focus:outline-none focus:ring-1 focus:ring-white/30 transition-all placeholder:text-white/20"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold tracking-widest uppercase text-white/30 ml-1">Context</label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., Photosynthesis"
                  className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-sm focus:outline-none focus:ring-1 focus:ring-white/30 transition-all placeholder:text-white/20"
                />
              </div>
            </div>

            {/* LEVEL SELECTION */}
            <div className="space-y-2">
              <label className="text-xs font-semibold tracking-widest uppercase text-white/30 ml-1">Cognitive Level</label>
              <div className="grid grid-cols-3 gap-3">
                {['high_school', 'undergraduate', 'postgraduate'].map((level) => (
                  <button
                    key={level}
                    type="button"
                    onClick={() => setStudentLevel(level)}
                    className={`
                      py-4 rounded-2xl text-xs font-medium border transition-all truncate
                      ${studentLevel === level 
                        ? 'bg-white text-black border-white' 
                        : 'bg-white/5 border-white/10 text-white/40 hover:border-white/30'}
                    `}
                  >
                    {level.replace('_', ' ').toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-200 text-sm"
              >
                <AlertCircle size={18} className="shrink-0 mt-0.5" />
                <p>{error}</p>
              </motion.div>
            )}

            <button
              type="submit"
              disabled={loading || !file}
              className={`
                group w-full py-5 rounded-[2rem] font-semibold text-lg transition-all flex items-center justify-center gap-3 overflow-hidden
                ${loading || !file 
                  ? 'bg-white/5 text-white/20 cursor-not-allowed' 
                  : 'bg-white text-black hover:bg-white/90 active:scale-[0.98] shadow-[0_20px_40px_rgba(255,255,255,0.1)]'}
              `}
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-black/20 border-t-black rounded-full animate-spin" />
                  Processing Knowledge...
                </>
              ) : (
                <>
                  Harvest Insights
                  <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* RECENT / INFO PANEL */}
        <div className="lg:col-span-5 space-y-6">
          {/* RESULTS PREVIEW */}
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="liquid-glass rounded-[2rem] p-8 space-y-8"
              >
                <div className="flex items-center justify-between">
                  <div className="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center text-white">
                    <CheckCircle2 size={24} />
                  </div>
                  <button onClick={() => setResult(null)} className="text-white/40 hover:text-white transition-colors">
                    <X size={20} />
                  </button>
                </div>

                <div>
                  <h3 className="text-3xl font-medium tracking-tighter mb-4 capitalize">
                    {result.study_package?.data?.summary?.title || "Harvest Complete"}
                  </h3>
                  <div className="space-y-6">
                    <div className="flex items-start gap-4 p-4 bg-white/5 rounded-2xl">
                      <BookOpen size={20} className="text-white/40 mt-1" />
                      <div>
                        <div className="text-xs text-white/30 uppercase tracking-widest font-bold mb-1">Leveled Summary</div>
                        <p className="text-sm text-white/70 line-clamp-3">
                          {result.study_package?.data?.summary?.content}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex gap-4">
                      <div className="flex-1 p-4 bg-white/5 rounded-2xl text-center">
                        <div className="text-2xl font-semibold mb-1">{result.study_package?.data?.flashcards?.length || 0}</div>
                        <div className="text-[10px] text-white/30 uppercase tracking-widest font-bold">Flashcards</div>
                      </div>
                      <div className="flex-1 p-4 bg-white/5 rounded-2xl text-center">
                        <div className="text-2xl font-semibold mb-1">{result.study_package?.data?.questions?.length || 0}</div>
                        <div className="text-[10px] text-white/30 uppercase tracking-widest font-bold">Questions</div>
                      </div>
                    </div>
                  </div>
                </div>

                <button 
                  onClick={() => onOpenArtifact(result.upload_id)}
                  className="w-full bg-white/10 hover:bg-white/20 py-4 rounded-2xl transition-all border border-white/5 flex items-center justify-center gap-2 group"
                >
                  Open Study Lab
                  <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </button>
              </motion.div>
            ) : (
              <div className="space-y-6">
                <div className="liquid-glass rounded-[2rem] p-8">
                  <h4 className="text-xs font-bold tracking-[0.2em] uppercase text-white/30 mb-6">Bloom Ecosystem</h4>
                  <div className="space-y-6">
                    <div className="flex gap-4 group cursor-help">
                      <div className="w-10 h-10 liquid-glass rounded-xl flex items-center justify-center shrink-0 border border-white/5">
                        <Library size={18} className="text-white/60" />
                      </div>
                      <div>
                        <h5 className="text-sm font-medium mb-1 group-hover:text-white transition-colors">Semantic Indexing</h5>
                        <p className="text-xs text-white/40 leading-relaxed">Our AI analyzes core nodes of knowledge to create a layered educational property framework.</p>
                      </div>
                    </div>
                    <div className="flex gap-4 group cursor-help">
                      <div className="w-10 h-10 liquid-glass rounded-xl flex items-center justify-center shrink-0 border border-white/5">
                        <HelpCircle size={18} className="text-white/60" />
                      </div>
                      <div>
                        <h5 className="text-sm font-medium mb-1 group-hover:text-white transition-colors">Active Recall</h5>
                        <p className="text-xs text-white/40 leading-relaxed">Generated flashcards and bloom-taxonomy questions reinforce long-term structural retention.</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-8 border border-white/5 bg-white/[0.02] rounded-[2rem] overflow-hidden relative group">
                  <div className="relative z-10">
                    <p className="text-sm leading-relaxed text-white/60 mb-6">
                      "We imagined a realm where learning has <em>no ending</em>, where every artifact becomes a seed."
                    </p>
                    <div className="flex items-center gap-4">
                      <div className="h-px flex-1 bg-white/10" />
                      <span className="text-[10px] tracking-widest font-bold text-white/20 uppercase">Core Ethos</span>
                      <div className="h-px flex-1 bg-white/10" />
                    </div>
                  </div>
                  <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-white/10 transition-colors" />
                </div>
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
