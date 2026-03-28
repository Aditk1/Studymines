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

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const res = await axios.get('/api/v1/lms/classrooms') // Mapping to classrooms for now
        setCourses(res.data)
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
        setCourses([...courses, { id: res.data.course_id, name: newCourseName, subject: "General" }])
        setIsCreating(false)
        setNewCourseName('')
    } catch (err) {
        console.error("Creation failed", err)
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

  if (loading) return <div className="h-full flex items-center justify-center">Loading Studio...</div>

  return (
    <div className="h-full flex flex-col gap-10">
      <header className="flex items-center justify-between">
        <div>
           <h2 className="text-4xl font-medium tracking-tighter">Instructor <em className="text-white/60">Studio</em></h2>
           <p className="text-white/30 text-lg">Architect your curriculum with RAG-enhanced modules.</p>
        </div>
        <button 
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2 bg-white text-black px-6 py-3 rounded-2xl font-bold hover:bg-white/90 transition-all"
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
                    <div className="text-[10px] tracking-widest uppercase text-white/20 ml-13">{course.subject || 'LMS CORE'}</div>
                </div>
            ))}
        </div>

        {/* EDITOR VIEW */}
        <div className="lg:col-span-8 liquid-glass-strong rounded-[2.5rem] p-10 flex flex-col">
            {selectedCourse ? (
                <>
                    <div className="flex items-center justify-between mb-10">
                        <div>
                            <h3 className="text-2xl font-medium tracking-tight mb-1">{selectedCourse.name}</h3>
                            <div className="flex items-center gap-4 text-xs text-white/40 font-medium">
                                <span className="flex items-center gap-1"><Layout size={12} /> 3 Sections</span>
                                <span className="flex items-center gap-1 text-white/60 font-bold uppercase tracking-widest"><Target size={12} /> Active Study</span>
                            </div>
                        </div>
                        <Settings size={20} className="text-white/20 hover:text-white cursor-pointer" />
                    </div>

                    <div className="flex-1 space-y-6 overflow-y-auto custom-scrollbar pr-4">
                        {selectedCourse.sections?.map((section, idx) => (
                            <div key={section.id} className="space-y-3">
                                <div className="flex items-center justify-between mb-2">
                                     <div className="flex items-center gap-3 text-[10px] font-bold tracking-[0.3em] uppercase text-white/20">
                                         <ChevronRight size={12} /> Section {idx + 1}: {section.title}
                                     </div>
                                     <button 
                                         onClick={async () => {
                                             const title = prompt("Module Title?")
                                             if(!title) return
                                             await axios.post(`/api/v1/lms/sections/${section.id}/modules`, {
                                                 title,
                                                 content_type: "document",
                                                 order: section.modules?.length || 0
                                             })
                                             // Refresh courses or just this course
                                             const res = await axios.get(`/api/v1/lms/courses/${selectedCourse.id}/modules`)
                                             setSelectedCourse({...selectedCourse, sections: res.data})
                                         }}
                                         className="text-[10px] font-bold uppercase tracking-widest text-white/20 hover:text-white transition-colors"
                                     >
                                         + Module
                                     </button>
                                </div>
                                {section.modules?.map((module) => (
                                    <div key={module.id} className="p-5 rounded-2xl bg-white/5 border border-white/5 flex items-center justify-between group">
                                        <div className="flex items-center gap-4">
                                            <div className="w-8 h-8 bg-white/5 rounded-lg flex items-center justify-center text-white/20">
                                                {module.type === 'video' ? <Plus size={16} /> : 
                                                 module.type === 'quiz' ? <Sparkles size={16} /> : 
                                                 <BookOpen size={16} />}
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-sm font-medium">{module.title}</span>
                                                <span className="text-[9px] text-white/20 font-bold uppercase tracking-widest">{module.type}</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button 
                                                onClick={() => generateQuiz(module.id)}
                                                className="text-[10px] font-bold uppercase tracking-wider bg-white/10 px-3 py-1.5 rounded-lg hover:bg-white/20 flex items-center gap-2"
                                            >
                                                <Sparkles size={12} /> AI Quiz
                                            </button>
                                            <MoreVertical size={16} className="text-white/20" />
                                        </div>
                                    </div>
                                ))}

                            </div>
                        ))}
                        {(!selectedCourse.sections || selectedCourse.sections.length === 0) && (
                            <div className="py-20 text-center text-white/10 italic text-sm">No modules architected for this course.</div>
                        )}
                    </div>

                    <div className="mt-8 pt-6 border-t border-white/5 flex gap-4 justify-end">
                         <button 
                             onClick={async () => {
                                 const title = prompt("Section Title?")
                                 if(!title) return
                                 await axios.post(`/api/v1/lms/courses/${selectedCourse.id}/sections`, {
                                     title,
                                     order: selectedCourse.sections?.length || 0
                                 })
                                 const res = await axios.get(`/api/v1/lms/courses/${selectedCourse.id}/modules`)
                                 setSelectedCourse({...selectedCourse, sections: res.data})
                             }}
                             className="flex items-center gap-2 bg-white/5 hover:bg-white/10 px-6 py-3 rounded-xl text-sm font-bold transition-all text-white/60"
                         >
                            Add Section
                         </button>
                         <button className="flex items-center gap-2 bg-white text-black px-6 py-3 rounded-xl text-sm font-bold transition-all shadow-xl">
                            Publish Architecture
                         </button>
                    </div>

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
