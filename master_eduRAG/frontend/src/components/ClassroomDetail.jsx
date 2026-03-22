import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, MessageSquare, Files, CheckSquare, Upload, Send, Hash, Settings, Users } from 'lucide-react'
import { supabase } from '../supabase'

const ChevronRight = ({ size, className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="m9 18 6-6-6-6"/></svg>
)

export default function ClassroomDetail({ classroomId, user, onBack, onOpenArtifact }) {
  const [activeTab, setActiveTab] = useState('materials') // 'materials', 'chat', 'exams'
  const [messages, setMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const ws = useRef(null)

  const [classroom, setClassroom] = useState(null)
  const [materials, setMaterials] = useState([])
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
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
    fetchData()
  }, [classroomId])

  useEffect(() => {
    if (activeTab === 'approvals' && classroomId) {
      const fetchRequests = async () => {
        try {
          const res = await axios.get(`/api/v1/lms/classrooms/${classroomId}/requests`)
          setRequests(res.data)
        } catch (err) {
          console.error("Failed to fetch requests", err)
        }
      }
      fetchRequests()
    }
  }, [activeTab, classroomId])

  const handleApprove = async (memberId) => {
    try {
      await axios.post(`/api/v1/lms/classrooms/${classroomId}/requests/${memberId}/approve`)
      setRequests(requests.filter(r => r.id !== memberId))
      alert('Student approved!')
    } catch (err) {
      console.error("Failed to approve student", err)
    }
  }

  // Handle Analytics/Material switching logic or WebSocket Connection for Chat/LMS
  useEffect(() => {
    if (activeTab === 'chat' && classroom?.chat_room_id) {
      // 1. Fetch History from Unified LMS Backend
      axios.get(`/api/v1/lms/chats/${classroom.chat_room_id}/history`)
        .then(res => setMessages(res.data || []))
        .catch(err => console.error("History fetch error:", err))

      // 2. Connect to the WebSocket Gateway
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/chat/${classroom.chat_room_id}`;
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => console.log("✓ Live connection established");
      
      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          setMessages(prev => [...(prev || []), msg]);
        } catch (e) {
          console.error("Parse error in websocket message", e);
        }
      };

      socket.onclose = () => console.log("⚠ Connection severed");
      ws.current = socket;

      return () => {
        if (ws.current) ws.current.close();
      };
    }
  }, [activeTab, classroom?.chat_room_id])

  const sendChatMessage = (e) => {
    e.preventDefault()
    if (!chatInput.trim() || !ws.current) return
    
    const payload = {
      sender_id: user.id,
      content: chatInput
    };

    try {
      ws.current.send(JSON.stringify(payload));
      setChatInput('')
    } catch (err) {
      console.error("Error sending message via WS", err)
    }
  }

  if (loading || !classroom) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col p-2">
      <header className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button 
            onClick={onBack}
            className="w-10 h-10 rounded-full liquid-glass flex items-center justify-center hover:bg-white/10 transition-colors"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-semibold tracking-tight">{classroom.name}</h2>
              <span className="px-2 py-0.5 rounded-full bg-white/10 text-[10px] font-bold tracking-wider uppercase text-white/60">
                {classroom.code}
              </span>
            </div>
            <p className="text-sm text-white/40">{classroom.subject}</p>
          </div>
        </div>
        
        <div className="flex bg-white/5 rounded-full p-1 liquid-glass border border-white/5">
          {['materials', 'chat', 'exams', ...(user?.role === 'teacher' ? ['approvals'] : [])].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-2 rounded-full text-sm font-medium capitalize transition-all ${
                activeTab === tab ? 'bg-white/10 text-white shadow-md' : 'text-white/40 hover:text-white/70'
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
            <motion.div
              key="materials"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="h-full overflow-y-auto custom-scrollbar pr-2"
            >
              {user?.role === 'teacher' && (
                <button className="w-full mb-6 border-2 border-dashed border-white/10 hover:border-white/30 rounded-2xl p-8 flex flex-col items-center justify-center gap-3 transition-colors text-white/40 hover:text-white/80 bg-white/[0.02] hover:bg-white/[0.05]">
                  <Upload size={24} />
                  <span className="font-medium text-sm">Smart Ingestion: Upload PDF/DOCX to generate Knowledge Graph</span>
                </button>
              )}
              
              <div className="grid grid-cols-1 gap-4">
                {materials.map((material) => (
                  <div 
                    key={material.id}
                    onClick={() => onOpenArtifact(material.id)}
                    className="liquid-glass rounded-2xl p-5 flex items-center justify-between cursor-pointer hover:bg-white/10 transition-colors border border-white/5"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
                        <Files size={20} />
                      </div>
                      <div>
                        <h4 className="font-semibold tracking-tight">{material.title}</h4>
                        <p className="text-xs text-white/40 mt-1">
                          Uploaded {new Date(material.created_at).toLocaleDateString()} • {material.status}
                        </p>
                      </div>
                    </div>
                    <ChevronRight size={18} className="text-white/20" />
                  </div>
                ))}
                {materials.length === 0 && (
                  <div className="text-center py-20 text-white/20 italic">
                    No materials uploaded yet.
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'chat' && (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="h-full flex flex-col liquid-glass rounded-3xl overflow-hidden border border-white/5"
            >
              <div className="bg-white/5 border-b border-white/5 p-4 flex items-center gap-3">
                <Hash size={18} className="text-white/40" />
                <h3 className="font-medium text-sm">General Classroom Discussion</h3>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                {messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-white/30 space-y-3">
                    <MessageSquare size={32} />
                    <p className="text-sm">No messages yet. Start the conversation!</p>
                  </div>
                ) : (
                  messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.sender_id === user.id ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[70%] rounded-2xl p-4 text-sm ${
                        msg.sender_id === user.id 
                          ? 'bg-blue-600/20 text-blue-50 border border-blue-500/20 rounded-br-sm' 
                          : 'bg-white/5 text-white/80 border border-white/5 rounded-bl-sm'
                      }`}>
                        {msg.content}
                      </div>
                    </div>
                  ))
                )}
              </div>

              <form onSubmit={sendChatMessage} className="p-4 bg-white/[0.02] border-t border-white/5">
                <div className="relative">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Message the classroom..."
                    className="w-full bg-white/5 border border-white/5 rounded-xl py-3 pl-4 pr-12 text-sm focus:bg-white/10 transition-all outline-none"
                  />
                  <button 
                    type="submit"
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center bg-white text-black rounded-lg hover:bg-white/90 transition-transform active:scale-95"
                  >
                    <Send size={14} />
                  </button>
                </div>
              </form>
            </motion.div>
          )}

          {activeTab === 'exams' && (
            <motion.div
              key="exams"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="h-full flex items-center justify-center text-white/40"
            >
              <div className="text-center space-y-4">
                <CheckSquare size={32} className="mx-auto text-white/20" />
                <p>AI-Assisted Exams module coming soon.</p>
              </div>
            </motion.div>
          )}

          {activeTab === 'approvals' && (
            <motion.div
              key="approvals"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="h-full overflow-y-auto custom-scrollbar pr-2"
            >
              <h3 className="text-xl font-medium mb-6">Pending Join Requests</h3>
              <div className="grid grid-cols-1 gap-4">
                {requests.map((request) => (
                  <div 
                    key={request.id}
                    className="liquid-glass rounded-2xl p-5 flex items-center justify-between border border-white/5"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center">
                        <Users size={20} />
                      </div>
                      <div>
                        <h4 className="font-semibold tracking-tight">{request.name}</h4>
                        <p className="text-xs text-white/40 mt-1">
                          Requested {new Date(request.requested_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <button 
                      onClick={() => handleApprove(request.id)}
                      className="px-4 py-2 bg-white text-black rounded-xl text-sm font-bold hover:bg-white/90 transition-all shadow-lg"
                    >
                      Approve
                    </button>
                  </div>
                ))}
                {requests.length === 0 && (
                  <div className="text-center py-20 text-white/20 italic">
                    No pending requests.
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
