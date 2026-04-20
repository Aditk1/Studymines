import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, X, Send, Bot, User, Loader2, Sparkles, BrainCircuit, Layers } from 'lucide-react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

export default function Chatbot({ user, uploadId }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Hello! I am your RLM-GraphRAG Cognitive Assistant powered by Llama 3. Ask me anything about your analyzed documents!" }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userText = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: userText }])
    setIsTyping(true)

    try {
      const formData = new FormData()
      formData.append('message', userText)
      if (uploadId) {
        formData.append('upload_id', uploadId)
      }

      const response = await axios.post('/api/v1/graph/chat', formData)

      if (response.data.success) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          text: response.data.answer,
          metadata: {
            strategy: response.data.strategy,
            graphStatus: response.data.graph_status,
            nodesVisited: response.data.nodes_visited,
            latency: response.data.latency_seconds
          }
        }])
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          text: `Error: ${response.data.error || 'Failed to query the knowledge graph.'}` 
        }])
      }
    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, { role: 'assistant', text: "Sorry, I encountered a connection error." }])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <>
      {/* FLOATING BUTTON */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-8 right-8 z-50 p-4 rounded-full bg-white text-black shadow-[0_0_30px_rgba(255,255,255,0.3)] hover:scale-110 active:scale-95 transition-all outline-none"
          >
            <BrainCircuit size={28} />
          </motion.button>
        )}
      </AnimatePresence>

      {/* CHAT WINDOW */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ 
              opacity: 1, 
              y: 0, 
              scale: 1,
              width: isExpanded ? 'calc(100% - 64px)' : '380px',
              height: isExpanded ? 'calc(100% - 64px)' : '600px',
              maxWidth: isExpanded ? '1200px' : '380px',
              left: isExpanded ? '50%' : 'auto',
              x: isExpanded ? '-50%' : '0%',
              bottom: isExpanded ? '32px' : '32px'
            }}
            exit={{ opacity: 0, y: 50, scale: 0.9 }}
            transition={{ type: "spring", damping: 25, stiffness: 300, layout: { duration: 0.4 } }}
            layout
            className="fixed bottom-8 right-8 z-50 flex flex-col liquid-glass-strong rounded-[2rem] overflow-hidden border border-white/10 shadow-2xl"
          >
            {/* CHAT HEADER */}
            <div className="px-6 py-5 bg-white/5 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full flex items-center justify-center bg-white/10 text-white">
                  <BrainCircuit size={20} />
                </div>
                <div>
                  <h3 className="font-semibold text-lg leading-none">Cognitive Core</h3>
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                    <span className="text-[10px] uppercase tracking-widest font-bold text-white/50">Llama 3 Connected</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button 
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="p-2 text-white/40 hover:text-white hover:bg-white/10 rounded-full transition-colors"
                  title={isExpanded ? "Minimize" : "Full Screen"}
                >
                  {isExpanded ? <X size={20} className="rotate-45" /> : <Layers size={20} />}
                </button>
                <button 
                  onClick={() => setIsOpen(false)}
                  className="p-2 text-white/40 hover:text-white hover:bg-white/10 rounded-full transition-colors"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* CHAT BODY */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-black/20">
              {messages.map((msg, idx) => (
                <motion.div 
                  key={idx}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`w-8 h-8 shrink-0 rounded-full flex items-center justify-center ${
                      msg.role === 'user' ? 'bg-white/10' : 'bg-white text-black'
                    }`}>
                      {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                    </div>
                    <div className="flex flex-col gap-1.5 mt-1">
                      <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                        msg.role === 'user' 
                          ? 'bg-white/10 text-white rounded-tr-sm border border-white/5' 
                          : 'bg-white/5 text-white/90 rounded-tl-sm border border-white/10'
                      }`}>
                        {msg.role === 'assistant' ? (
                          <div className="markdown-content prose-invert">
                            <ReactMarkdown>{msg.text}</ReactMarkdown>
                          </div>
                        ) : (
                          msg.text
                        )}
                      </div>

                      {msg.metadata && (
                        <div className="flex items-center gap-2 px-1 text-[9px] font-bold uppercase tracking-widest text-white/30">
                          <Sparkles size={10} />
                          <span>
                            {msg.metadata.strategy === 'stage_one_fallback' ? 'Stage 1 Fallback' : 'Graph Grounded'}
                            {' • '}
                            {msg.metadata.latency}s
                            {' • '}
                            Nodes: {msg.metadata.nodesVisited}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
              
              {isTyping && (
                <div className="flex justify-start">
                  <div className="flex gap-3 max-w-[80%]">
                    <div className="w-8 h-8 shrink-0 rounded-full flex items-center justify-center bg-white text-black">
                      <Bot size={14} />
                    </div>
                    <div className="px-5 py-4 rounded-xl rounded-tl-sm bg-white/5 border border-white/10 flex items-center gap-2 text-white/40">
                      <Loader2 size={16} className="animate-spin" />
                      <span className="text-xs font-medium">Navigating Knowledge Graph...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* CHAT INPUT */}
            <form onSubmit={handleSend} className="p-4 bg-white/5 border-t border-white/10 relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={uploadId ? "Ask about this document..." : "Ask the global knowledge graph..."}
                className="w-full bg-black/40 border border-white/10 rounded-2xl pl-5 pr-14 py-4 text-sm text-white placeholder-white/30 focus:outline-none focus:border-white/30 focus:bg-black/60 transition-all font-medium"
                disabled={isTyping}
              />
              <button 
                type="submit"
                disabled={!input.trim() || isTyping}
                className="absolute right-6 top-1/2 -translate-y-1/2 p-2.5 bg-white text-black rounded-xl hover:bg-white/90 disabled:opacity-50 disabled:hover:bg-white transition-all outline-none"
              >
                <Send size={16} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
