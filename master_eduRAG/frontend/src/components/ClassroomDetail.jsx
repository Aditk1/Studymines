import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ArrowLeft, MessageSquare, Files, CheckSquare, 
  Upload, Send, Hash, Settings, Users, 
  Sparkles, Plus, Clock, FileText, ChevronRight 
} from 'lucide-react'

export default function ClassroomDetail({ classroomId, user, onBack, onOpenArtifact }) {
  const [activeTab, setActiveTab] = useState('materials') // 'materials', 'chat', 'exams', 'approvals'
  const [messages, setMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const ws = useRef(null)

  const [classroom, setClassroom] = useState(null)
  const [materials, setMaterials] = useState([])
  const [exams, setExams] = useState([])
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [showGenModal, setShowGenModal] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    const fetchBaseData = async () => {
      try {
        const [clsRes, matRes] = await Promise.all([
          axios.get(`/api/v1/lms/classrooms/${classroomId}`),
          axios.get(`/api/v1/lms/classrooms/${classroomId}/materials`)
        ])
        setClassroom(clsRes.data)
        setMaterials(matRes.data)
      } catch (err) {
        console.error("Failed to fetch classroom data", err)
      } finally {
        setLoading(false)
      }
    }
    fetchBaseData()
  }, [classroomId])

  useEffect(() => {
    if (activeTab === 'exams') fetchExams()
    if (activeTab === 'approvals') fetchRequests()
  }, [activeTab])

  const fetchExams = async () => {
    try {
        const res = await axios.get(`/api/v1/lms/classrooms/${classroomId}/exams`)
        setExams(res.data)
    } catch (err) {
        console.error("Failed to fetch exams", err)
    }
  }

  const fetchRequests = async () => {
    try {
      const res = await axios.get(`/api/v1/lms/classrooms/${classroomId}/requests`)
      setRequests(res.data)
    } catch (err) {
      console.error("Failed to fetch requests", err)
    }
  }

  const handleGenerateExam = async (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    setGenerating(true)
    try {
        await axios.post('/api/v1/lms/exams/generate', {
            title: formData.get('title'),
            topic: formData.get('topic') || classroom.subject,
            num_questions: parseInt(formData.get('num')),
            classroom_id: classroomId,
            context_type: formData.get('context')
        })
        setShowGenModal(false)
        fetchExams()
        alert("CognitiveAIGenerator has successfully architected the exam!")
    } catch (err) {
        console.error("Exam generation failed", err)
    } finally {
        setGenerating(false)
    }
  }

  const handleApprove = async (memberId) => {
    try {
      await axios.post(`/api/v1/lms/classrooms/${classroomId}/requests/${memberId}/approve`)
      setRequests(requests.filter(r => r.id !== memberId))
      alert('Student approved!')
    } catch (err) {
      console.error("Failed to approve student", err)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('classroom_id', classroomId);
    formData.append('title', file.name.split('.')[0]); 

    try {
      const res = await axios.post('/api/v1/lms/materials/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (res.data.success) {
        const matRes = await axios.get(`/api/v1/lms/classrooms/${classroomId}/materials`);
        setMaterials(matRes.data);
      }
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setUploading(false);
      e.target.value = null; 
    }
  };

  useEffect(() => {
    if (activeTab === 'chat' && classroom?.chat_room_id) {
      axios.get(`/api/v1/lms/chats/${classroom.chat_room_id}/history`)
        .then(res => setMessages(res.data || []))
        .catch(err => console.error("History fetch error:", err))

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/chat/${classroom.chat_room_id}`;
      const socket = new WebSocket(wsUrl);
      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          setMessages(prev => [...(prev || []), msg]);
        } catch (e) {}
      };
      ws.current = socket;
      return () => { if (ws.current) ws.current.close(); };
    }
  }, [activeTab, classroom?.chat_room_id])

  const sendChatMessage = (e) => {
    e.preventDefault()
    if (!chatInput.trim() || !ws.current) return
    const payload = { sender_id: user.id, content: chatInput, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, payload]);
    setChatInput('')
    try { ws.current.send(JSON.stringify(payload)); } catch (err) {}
  }

  if (loading || !classroom) {
    return <div className="h-full flex items-center justify-center"><div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" /></div>
  }

  return (
    <div className="h-full flex flex-col p-2">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
        <div className="flex items-center gap-6">
          <button onClick={onBack} className="w-12 h-12 rounded-2xl liquid-glass flex items-center justify-center hover:bg-white/10 transition-all border border-white/10">
            <ArrowLeft size={20} />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-3xl font-medium tracking-tighter">{classroom.name}</h2>
              <span className="px-3 py-1 bg-white/10 rounded-full text-[10px] font-bold tracking-widest uppercase text-white/50 border border-white/10">{classroom.code}</span>
            </div>
            <p className="text-sm text-white/30 tracking-tight">{classroom.subject} • Cognitive Instance</p>
          </div>
        </div>
        
        <div className="flex bg-white/5 rounded-2xl p-1.5 liquid-glass border border-white/10">
          {['materials', 'chat', 'exams', ...(user?.role === 'teacher' ? ['approvals'] : [])].map(tab => (
            <button
              key={tab} onClick={() => setActiveTab(tab)}
              className={`px-6 py-2.5 rounded-xl text-xs font-bold uppercase tracking-widest transition-all ${
                activeTab === tab ? 'bg-white text-black shadow-xl scale-105' : 'text-white/30 hover:text-white/60'
              }`}
            >
              <div className="flex items-center gap-2">
                {tab === 'materials' && <Files size={14} />}
                {tab === 'chat' && <MessageSquare size={14} />}
                {tab === 'exams' && <CheckSquare size={14} />}
                {tab === 'approvals' && <Users size={14} />}
                {tab}
              </div>
            </button>
          ))}
        </div>
      </header>

      <div className="flex-1 overflow-hidden relative">
        <AnimatePresence mode="wait">
          {activeTab === 'materials' && (
            <motion.div key="materials" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="h-full overflow-y-auto custom-scrollbar pr-2">
              {user?.role === 'teacher' && (
                <>
                  <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileUpload} accept=".pdf,.docx,.txt" />
                  <button 
                    onClick={() => fileInputRef.current?.click()} disabled={uploading}
                    className="w-full mb-6 border-2 border-dashed border-white/10 hover:border-white/30 rounded-3xl p-10 flex flex-col items-center justify-center gap-4 transition-all text-white/40 hover:text-white/80 bg-white/[0.01] hover:bg-white/[0.04] disabled:opacity-50 group"
                  >
                    {uploading ? (
                      <div className="flex items-center gap-4"><div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" /><span className="font-bold tracking-widest uppercase text-xs">Ingesting Graph Nodes...</span></div>
                    ) : (
                      <><Upload size={32} className="group-hover:scale-110 transition-transform" /><span className="font-bold uppercase tracking-widest text-[10px]">Ingest Document (RAG Core)</span></>
                    )}
                  </button>
                </>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {materials.map(mat => (
                  <div key={mat.id} onClick={() => onOpenArtifact(mat.id)} className="liquid-glass rounded-3xl p-6 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-all border border-white/5 group">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center group-hover:bg-indigo-500/20 transition-colors"><FileText size={22} /></div>
                      <div>
                        <h4 className="font-semibold">{mat.title}</h4>
                        <p className="text-[10px] text-white/20 mt-1 uppercase font-bold tracking-wider">{new Date(mat.created_at).toLocaleDateString()} • {mat.status}</p>
                      </div>
                    </div>
                    <ChevronRight size={18} className="text-white/10 group-hover:text-white transition-colors" />
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'chat' && (
            <motion.div key="chat" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="h-full flex flex-col liquid-glass rounded-[2rem] overflow-hidden border border-white/10">
              <div className="bg-white/5 border-b border-white/10 p-5 flex items-center justify-between">
                <div className="flex items-center gap-3"><Hash size={18} className="text-white/40" /><h3 className="font-bold uppercase tracking-widest text-xs">General Discussion</h3></div>
              </div>
              <div className="flex-1 overflow-y-auto p-8 space-y-6 custom-scrollbar">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.sender_id === user.id ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[75%] rounded-2xl p-5 text-sm ${msg.sender_id === user.id ? 'bg-indigo-600/20 text-indigo-50 border border-indigo-500/30 rounded-br-sm shadow-xl' : 'bg-white/5 text-white/80 border border-white/10 rounded-bl-sm'}`}>{msg.content}</div>
                  </div>
                ))}
              </div>
              <form onSubmit={sendChatMessage} className="p-6 bg-white/[0.02] border-t border-white/10">
                <div className="relative"><input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Send a message to the cohort..." className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-6 pr-14 text-sm focus:bg-white/10 transition-all outline-none" /><button type="submit" className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 flex items-center justify-center bg-white text-black rounded-xl hover:scale-105 active:scale-95 transition-all shadow-xl"><Send size={16} /></button></div>
              </form>
            </motion.div>
          )}

          {activeTab === 'exams' && (
            <motion.div key="exams" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="h-full flex flex-col sapce-y-6">
              <div className="flex items-center justify-between mb-8">
                <div>
                   <h3 className="text-xl font-medium tracking-tight">Active Assessments</h3>
                   <p className="text-xs text-white/40 mt-1">AI-architected quizzes for this classroom.</p>
                </div>
                {user?.role === 'teacher' && (
                    <button 
                        onClick={() => setShowGenModal(true)}
                        className="flex items-center gap-2 bg-indigo-500 text-white px-5 py-2.5 rounded-2xl font-bold text-xs uppercase tracking-widest hover:bg-indigo-400 transition-all shadow-[0_0_20px_rgba(99,102,241,0.3)]"
                    >
                        <Sparkles size={16} /> Architect AI Exam
                    </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 overflow-y-auto custom-scrollbar pr-2 pb-10">
                {exams.map(exam => (
                    <div key={exam.id} className="liquid-glass rounded-3xl p-6 border border-white/5 hover:border-white/20 transition-all group">
                        <div className="flex items-center justify-between mb-4">
                            <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-400 flex items-center justify-center"><CheckSquare size={20} /></div>
                            <span className="text-[9px] font-bold uppercase tracking-widest text-white/20">{new Date(exam.created_at).toLocaleDateString()}</span>
                        </div>
                        <h4 className="font-semibold text-lg mb-1">{exam.title}</h4>
                        <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest text-white/30 mb-6">
                            <span>{exam.points} Points</span>
                            <span className="w-1 h-1 rounded-full bg-white/20" />
                            <span className={exam.is_published ? 'text-green-400' : 'text-orange-400'}>{exam.is_published ? 'Active' : 'Draft'}</span>
                        </div>
                        <button className="w-full bg-white/5 hover:bg-white text-white/40 hover:text-black py-3 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all">Launch Preview</button>
                    </div>
                ))}
                {exams.length === 0 && (
                    <div className="col-span-full py-20 text-center text-white/10 italic">No exams architected yet. Let AI build your first quiz.</div>
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'approvals' && (
            <motion.div key="approvals" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} className="h-full overflow-y-auto custom-scrollbar pr-2">
              <h3 className="text-xl font-medium mb-6">Pending Join Requests</h3>
              <div className="space-y-4">
                {requests.map(req => (
                  <div key={req.id} className="liquid-glass rounded-3xl p-6 flex items-center justify-between border border-white/5">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-purple-500/10 text-purple-400 flex items-center justify-center"><Users size={22} /></div>
                      <div>
                        <h4 className="font-bold">{req.name}</h4>
                        <p className="text-[10px] text-white/30 uppercase font-bold tracking-widest mt-1">Requested {new Date(req.requested_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <button onClick={() => handleApprove(req.id)} className="px-6 py-3 bg-white text-black rounded-2xl text-[10px] font-bold uppercase tracking-widest hover:scale-105 transition-all shadow-xl">Approve</button>
                  </div>
                ))}
                {requests.length === 0 && <div className="text-center py-20 text-white/10 italic">No pending cohort requests.</div>}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {showGenModal && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[300] bg-black/80 backdrop-blur-md flex items-center justify-center p-6">
                <motion.form 
                    initial={{ y: 20, scale: 0.95 }} animate={{ y: 0, scale: 1 }}
                    onSubmit={handleGenerateExam}
                    className="w-full max-w-lg liquid-glass-strong p-10 rounded-[2.5rem] border border-white/10 space-y-6"
                >
                    <div className="flex items-center gap-4 mb-2">
                        <div className="p-3 bg-indigo-500/20 text-indigo-400 rounded-2xl shadow-inner"><Sparkles size={24} /></div>
                        <h3 className="text-2xl font-medium">Cognitive AIGenerator</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="space-y-1">
                            <label className="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-2">Assessment Title</label>
                            <input required name="title" className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-sm focus:border-indigo-500/50 outline-none transition-all" placeholder="e.g. Midterm Mastery Check" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-2">Topic Focus</label>
                                <input name="topic" className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-sm focus:border-indigo-500/50 outline-none transition-all" defaultValue={classroom.subject} />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-2">Question Count</label>
                                <input required name="num" type="number" min="1" max="20" defaultValue="5" className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-sm focus:border-indigo-500/50 outline-none transition-all" />
                            </div>
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-bold uppercase tracking-widest text-white/30 ml-2">Knowledge Source</label>
                            <select name="context" className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-sm focus:border-indigo-500/50 outline-none appearance-none cursor-pointer">
                                <option value="general" className="bg-zinc-900">Ecosystem Knowledge (Global Llama 3)</option>
                                <option value="document" className="bg-zinc-900">Ground via Classroom Materials (RAG)</option>
                                <option value="mastery" className="bg-zinc-900">Target Student Weak Areas (Graph Core)</option>
                            </select>
                        </div>
                    </div>
                    <div className="flex gap-4 pt-4">
                        <button type="button" onClick={() => setShowGenModal(false)} className="flex-1 py-4 text-xs font-bold uppercase tracking-widest text-white/20 hover:text-white transition-colors">Abort</button>
                        <button type="submit" disabled={generating} className="flex-1 bg-white text-black py-4 rounded-2xl text-xs font-bold uppercase tracking-widest shadow-2xl hover:bg-indigo-100 disabled:opacity-50">
                            {generating ? 'Architecting...' : 'Construct Exam'}
                        </button>
                    </div>
                </motion.form>
            </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
