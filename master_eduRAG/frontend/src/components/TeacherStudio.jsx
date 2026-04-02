import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Plus, 
  Folder, 
  Settings, 
  MoreVertical, 
  Sparkles, 
  Layout, 
  BookOpen, 
  ChevronRight,
  Target,
  PenTool
} from 'lucide-react'

export default function TeacherStudio({ user }) {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedCourse, setSelectedCourse] = useState(null)
  const [isCreating, setIsCreating] = useState(false)
  const [newCourseName, setNewCourseName] = useState('')
  const [library, setLibrary] = useState([])
  const [isArchitecting, setIsArchitecting] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const [courseRes, libraryRes] = await Promise.all([
          axios.get('/api/v1/lms/courses'),
          axios.get('/api/v1/uploads/all')
        ])
        setCourses(courseRes.data)
        setLibrary(libraryRes.data)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchCourses()
  }, [])

  const handleCreateCourse = async () => {
    if (!newCourseName) return
    try {
        const res = await axios.post('/api/v1/lms/courses', {
            title: newCourseName,
            description: "A specialized AI-powered learning path."
        })
        const newCourse = { id: res.data.course_id, name: newCourseName, subject: "General" }
        setCourses([...courses, newCourse])
        setSelectedCourse(newCourse)
        setIsCreating(false)
        setNewCourseName('')
    } catch (err) {
        console.error("Creation failed", err)
    }
  }

  const handleAIArchitect = async (artifactId) => {
      setIsArchitecting(true)
      try {
          await axios.post(`/api/v1/lms/studio/ai-architect/${selectedCourse.id}`, { artifact_id: artifactId })
          const res = await axios.get(`/api/v1/lms/courses/${selectedCourse.id}/modules`)
          setSelectedCourse({...selectedCourse, sections: res.data})
          setIsArchitecting(false)
      } catch (err) {
          console.error("Architecting failed", err)
          setIsArchitecting(false)
      }
  }

  const handlePublish = async () => {
      setIsPublishing(true)
      try {
          await axios.post(`/api/v1/lms/studio/publish-architecture/${selectedCourse.id}`)
          alert("Course published successfully!")
          setIsPublishing(false)
      } catch (err) {
          console.error("Publishing failed", err)
          setIsPublishing(false)
      }
  }

  const generateQuiz = async (materialId) => {
      try {
          await axios.post(`/api/v1/lms/studio/generate-quiz?material_id=${materialId}`)
          alert("AI Questions generated for this module!")
      } catch (err) {
          console.error("Generation failed", err)
      }
  }

  if (loading) return <div className="h-full flex items-center justify-center text-white/20 uppercase tracking-widest text-xs font-bold">Initializing Studio...</div>

  return (
    <div className="h-full flex flex-col gap-10">
      <header className="flex items-center justify-between">
        <div>
           <h2 className="text-4xl font-medium tracking-tighter">Instructor <em className="text-white/60">Studio</em></h2>
           <p className="text-white/30 text-lg">Architect your curriculum with RAG-enhanced modules.</p>
        </div>
        <button 
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2 bg-white text-black px-6 py-3 rounded-2xl font-bold hover:bg-white/90 transition-all shadow-[0_10px_30px_rgba(255,255,255,0.1)]"
        >
            <Plus size={18} />
            Build Course
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1 overflow-hidden">
        {/* COURSE LIST */}
        <div className="lg:col-span-4 space-y-4 overflow-y-auto pr-2 custom-scrollbar">
            {courses.map((course) => (
                <div 
                    key={course.id}
                    onClick={async () => {
                        try {
                            const res = await axios.get(`/api/v1/lms/courses/${course.id}/modules`)
                            setSelectedCourse({...course, sections: res.data})
                        } catch (err) {
                            setSelectedCourse(course)
                        }
                    }}
                    className={`p-6 rounded-3xl border transition-all cursor-pointer group
                        ${selectedCourse?.id === course.id ? 'bg-white/10 border-white/20' : 'bg-white/[0.02] border-white/5 hover:bg-white/5'}
                    `}
                >
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 liquid-glass rounded-xl flex items-center justify-center text-white/40 group-hover:text-white transition-colors">
                                <PenTool size={18} />
                            </div>
                            <h4 className="font-semibold text-white/90">{course.name}</h4>
                        </div>
                        <ChevronRight size={16} className={`transition-transform ${selectedCourse?.id === course.id ? 'rotate-90' : 'opacity-20'}`} />
                    </div>
                    <div className="text-[10px] tracking-widest uppercase text-white/20 ml-13 font-bold">{course.subject || 'LMS CORE'}</div>
                </div>
            ))}
        </div>

        {/* EDITOR VIEW */}
        <div className="lg:col-span-8 liquid-glass-strong rounded-[2.5rem] p-10 flex flex-col relative overflow-hidden">
            {selectedCourse ? (
                <>
                    <div className="flex items-center justify-between mb-10">
                        <div>
                            <h3 className="text-2xl font-medium tracking-tight mb-1">{selectedCourse.name}</h3>
                            <div className="flex items-center gap-4 text-xs text-white/40 font-medium">
                                <span className="flex items-center gap-1"><Layout size={12} /> {selectedCourse.sections?.length || 0} Sections</span>
                                <span className="flex items-center gap-1 text-white/60 font-bold uppercase tracking-widest"><Target size={12} /> Active Study</span>
                            </div>
                        </div>
                        <Settings size={20} className="text-white/20 hover:text-white cursor-pointer" />
                    </div>

                    <div className="flex-1 space-y-8 overflow-y-auto custom-scrollbar pr-4">
                        {selectedCourse.sections?.map((section, idx) => (
                            <div key={section.id} className="space-y-4">
                                <div className="flex items-center justify-between">
                                     <div className="flex items-center gap-3 text-[10px] font-bold tracking-[0.3em] uppercase text-white/20">
                                         <span className="w-6 h-6 rounded-lg bg-white/5 flex items-center justify-center text-[8px]">{idx + 1}</span> 
                                         {section.title}
                                     </div>
                                     <button 
                                         onClick={async () => {
                                             const title = prompt("Module Title?")
                                             if(!title) return
                                             try {
                                                 await axios.post(`/api/v1/lms/sections/${section.id}/modules`, {
                                                     title,
                                                     content_type: "document",
                                                     order: section.modules?.length || 0
                                                 })
                                                 const res = await axios.get(`/api/v1/lms/courses/${selectedCourse.id}/modules`)
                                                 setSelectedCourse({...selectedCourse, sections: res.data})
                                             } catch (err) {
                                                 console.error(err)
                                             }
                                         }}
                                         className="text-[10px] font-bold uppercase tracking-widest text-white/20 hover:text-indigo-400 transition-colors"
                                     >
                                         + Module
                                     </button>
                                </div>
                                <div className="grid grid-cols-1 gap-3">
                                    {section.modules?.map((module) => (
                                        <div key={module.id} className="p-5 rounded-2xl bg-white/[0.03] border border-white/5 flex items-center justify-between group hover:bg-white/[0.06] transition-all">
                                            <div className="flex items-center gap-4">
                                                <div className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center text-white/30 group-hover:text-white transition-colors">
                                                    {module.type === 'video' ? <Plus size={18} /> : 
                                                     module.type === 'quiz' ? <Sparkles size={18} /> : 
                                                     <BookOpen size={18} />}
                                                </div>
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-semibold text-white/80">{module.title}</span>
                                                    <span className="text-[9px] text-white/20 font-bold uppercase tracking-[.2em] mt-0.5">{module.type}</span>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button 
                                                    onClick={() => generateQuiz(module.id)}
                                                    className="text-[9px] font-bold uppercase tracking-widest bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-3 py-2 rounded-xl hover:bg-indigo-500/40 flex items-center gap-2 transition-all"
                                                >
                                                    <Sparkles size={12} /> AI Quiz
                                                </button>
                                                <button className="h-10 w-10 flex items-center justify-center text-white/20 hover:text-white transition-colors">
                                                    <MoreVertical size={16} />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                        {(!selectedCourse.sections || selectedCourse.sections.length === 0) && (
                            <div className="py-20 flex flex-col items-center text-center">
                                <div className="w-16 h-16 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 mb-6">
                                    <Sparkles size={32} />
                                </div>
                                <h4 className="text-lg font-medium text-white/60 mb-2">No infrastructure built yet</h4>
                                <p className="text-white/20 text-sm max-w-sm mb-8">Choose an artifact from your library to let the AI architect your curriculum automatically.</p>
                                
                                <div className="w-full max-w-md space-y-2">
                                    <div className="text-[9px] font-bold uppercase tracking-widest text-white/10 text-left mb-2 ml-2">Available Artifacts</div>
                                    {library.length > 0 ? library.slice(0, 3).map(art => (
                                        <button 
                                            key={art.id}
                                            onClick={() => handleAIArchitect(art.id)}
                                            className="w-full p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-white/20 flex items-center justify-between group transition-all"
                                        >
                                            <div className="flex items-center gap-3">
                                                <BookOpen size={16} className="text-white/20" />
                                                <span className="text-sm text-white/60">{art.file_name}</span>
                                            </div>
                                            <Sparkles size={14} className="text-white/10 group-hover:text-indigo-400" />
                                        </button>
                                    )) : (
                                        <div className="text-xs text-white/10 italic">No artifacts found in library.</div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="mt-8 pt-6 border-t border-white/5 flex gap-4 justify-end">
                         <button 
                             onClick={async () => {
                                 const title = prompt("Section Title?")
                                 if(!title) return
                                 try {
                                     await axios.post(`/api/v1/lms/courses/${selectedCourse.id}/sections`, {
                                         title,
                                         order: selectedCourse.sections?.length || 0
                                     })
                                     const res = await axios.get(`/api/v1/lms/courses/${selectedCourse.id}/modules`)
                                     setSelectedCourse({...selectedCourse, sections: res.data})
                                 } catch(err) {
                                     console.error(err)
                                 }
                             }}
                             className="flex items-center gap-2 bg-white/5 hover:bg-white/10 px-6 py-4 rounded-2xl text-xs font-bold uppercase tracking-widest transition-all text-white/40 hover:text-white"
                         >
                            Add Section
                         </button>
                         <button 
                             disabled={isPublishing || !selectedCourse.sections?.length}
                             onClick={handlePublish}
                             className="flex items-center gap-2 bg-white text-black px-8 py-4 rounded-2xl text-xs font-black uppercase tracking-[0.2em] transition-all shadow-[0_15px_30px_rgba(0,0,0,0.4)] hover:scale-[1.02] disabled:opacity-50 disabled:grayscale"
                         >
                            {isPublishing ? "Publishing..." : "Publish Architecture"}
                         </button>
                    </div>

                    {isArchitecting && (
                        <div className="absolute inset-0 z-50 bg-[#121212]/80 backdrop-blur-xl flex flex-col items-center justify-center p-10 text-center">
                            <motion.div 
                                animate={{ scale: [1, 1.1, 1], opacity: [0.5, 1, 0.5] }}
                                transition={{ repeat: Infinity, duration: 2 }}
                                className="w-16 h-16 bg-indigo-500 rounded-full flex items-center justify-center text-white mb-6 shadow-[0_0_50px_rgba(99,102,241,0.5)]"
                            >
                                <Sparkles size={32} />
                            </motion.div>
                            <h3 className="text-xl font-bold mb-2">AI is Architecting...</h3>
                            <p className="text-white/40 text-sm max-w-xs">Deconstructing artifact taxonomies and mapping cognitive paths for this course.</p>
                        </div>
                    )}
                </>
            ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                    <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center text-white/10 mb-6">
                        <Folder size={40} />
                    </div>
                    <h3 className="text-xl font-medium text-white/60">Select a course to begin architecture</h3>
                    <p className="text-white/20 text-sm max-w-xs mt-2">Design cognitive paths and map-reduce logic for your students.</p>
                </div>
            )}
        </div>
      </div>

      <AnimatePresence>
        {isCreating && (
            <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-md flex items-center justify-center p-6"
            >
                <div className="w-full max-w-md liquid-glass-strong p-10 rounded-[2rem] border border-white/10">
                    <h3 className="text-2xl font-medium mb-6">Create AI Course</h3>
                    <input 
                        type="text" value={newCourseName} onChange={(e) => setNewCourseName(e.target.value)}
                        placeholder="e.g. LLM Foundations"
                        className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-white focus:outline-none focus:border-white/40 mb-8"
                    />
                    <div className="flex gap-4">
                        <button onClick={() => setIsCreating(false)} className="flex-1 py-4 text-sm font-bold text-white/40">Cancel</button>
                        <button onClick={handleCreateCourse} className="flex-1 bg-white text-black py-4 rounded-2xl text-sm font-bold">Construct</button>
                    </div>
                </div>
            </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
