import { useEffect, useState, useRef } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Sparkles, Target, Zap } from 'lucide-react'

export default function KnowledgeMap({ userId, uploadId, onSelectConcept }) {
  const [data, setData] = useState({ nodes: [], links: [] })
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState(null)
  const fgRef = useRef()

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const response = await axios.get('/api/v1/lms/mastery-view', {
          params: { user_id: userId, upload_id: uploadId }
        })
        
        // Transform Mastery Map into D3 Force Format
        const nodes = response.data.map((ent, idx) => ({
          id: ent.name || `node-${idx}`,
          name: ent.name || "Unknown",
          val: 10 + (ent.mastery * 10), // Node size by mastery
          mastery: ent.mastery || 0,
          type: ent.type,
          community: ent.community
        }))

        // Mocking some links if they don't exist in the data list
        const links = []
        for(let i=0; i < nodes.length - 1; i++) {
            if (nodes[i].community === nodes[i+1].community) {
                links.push({ source: nodes[i].id, target: nodes[i+1].id })
            } else if (i % 3 === 0) {
                // Cross-community bridges
                links.push({ source: nodes[i].id, target: nodes[i+1].id })
            }
        }

        setData({ nodes, links })
      } catch (err) {
        console.error("Failed to fetch graph", err)
      } finally {
        setLoading(false)
      }
    }
    fetchGraph()
  }, [userId, uploadId])

  const getMasteryColor = (mastery) => {
    if (mastery >= 0.8) return '#10b981' // Green
    if (mastery >= 0.5) return '#f59e0b' // Amber
    return '#ef4444' // Red
  }

  const handleNodeClick = (node) => {
    setSelectedNode(node)
    // Center view on node
    if (fgRef.current) {
        fgRef.current.centerAt(node.x, node.y, 400)
        fgRef.current.zoom(2.5, 400)
    }
  }

  if (loading) {
      return (
        <div className="h-full flex items-center justify-center bg-black/40 rounded-[2.5rem] backdrop-blur-xl">
             <div className="animate-pulse text-white/40 tracking-widest uppercase text-xs font-bold font-poppins">Synchronizing Cognitive Topology...</div>
        </div>
      )
  }

  return (
    <div className="relative w-full h-full bg-black/20 rounded-[2.5rem] overflow-hidden border border-white/5 shadow-2xl">
      <ForceGraph2D
        ref={fgRef}
        graphData={data}
        nodeLabel="name"
        nodeColor={node => getMasteryColor(node.mastery)}
        nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 12/globalScale;
            ctx.font = `${fontSize}px Inter`;
            const textWidth = ctx.measureText(label).width;
            const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2); 

            // Draw shadow/glow
            ctx.shadowBlur = 15;
            ctx.shadowColor = getMasteryColor(node.mastery);
            
            // Draw circle
            ctx.fillStyle = getMasteryColor(node.mastery);
            ctx.beginPath(); 
            ctx.arc(node.x, node.y, 4, 0, 2 * Math.PI, false); 
            ctx.fill();

            // Reset shadow
            ctx.shadowBlur = 0;

            // Label text only on high zoom
            if (globalScale > 1.5) {
                ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
                ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2 - 8, ...bckgDimensions);
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = 'white';
                ctx.fillText(label, node.x, node.y - 8);
            }
        }}
        linkColor={() => 'rgba(255,255,255,0.08)'}
        linkWidth={1}
        onNodeClick={handleNodeClick}
        cooldownTicks={100}
      />

      {/* OVERLAY: NODE DETAILS */}
      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            className="absolute top-6 right-6 w-[320px] liquid-glass-strong border border-white/10 rounded-3xl p-8 z-50 shadow-2xl"
          >
            <button 
              onClick={() => setSelectedNode(null)}
              className="absolute top-4 right-4 text-white/20 hover:text-white transition-colors"
            >
              <X size={20} />
            </button>

            <div className="flex items-center gap-3 mb-6">
                <div 
                    className="w-4 h-4 rounded-full shadow-[0_0_15px_rgba(255,255,255,0.2)]"
                    style={{ backgroundColor: getMasteryColor(selectedNode.mastery) }}
                />
                <h3 className="text-xl font-medium tracking-tighter truncate">{selectedNode.name}</h3>
            </div>

            <div className="space-y-6">
                <div>
                    <div className="text-[10px] font-bold tracking-[0.2em] uppercase text-white/30 mb-2">Mastery Index</div>
                    <div className="flex items-end gap-2">
                        <span className="text-3xl font-semibold">{(selectedNode.mastery * 100).toFixed(1)}%</span>
                        <Target size={16} className="mb-2 text-white/20" />
                    </div>
                </div>

                <div className="p-4 bg-white/10 border border-white/5 rounded-2xl">
                    <p className="text-sm text-white/50 leading-relaxed italic">
                        "{selectedNode.type || 'Cognitive Node'}: High centrality in local community {selectedNode.community}."
                    </p>
                </div>

                <button 
                    onClick={() => onSelectConcept(selectedNode.name)}
                    className="w-full bg-white text-black py-4 rounded-2xl text-sm font-bold flex items-center justify-center gap-2 hover:bg-white/90 active:scale-95 transition-all shadow-xl"
                >
                    <Sparkles size={16} />
                    AI Explainer
                </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="absolute top-6 left-6 pointer-events-none">
        <h4 className="text-xs font-bold tracking-[0.3em] uppercase text-white/30 flex items-center gap-2">
            <Zap size={14} className="animate-pulse" /> Cognitive Topology
        </h4>
        <div className="text-[10px] font-medium text-white/20 mt-1 uppercase tracking-widest">
            {data.nodes.length} Neural Intersections
        </div>
      </div>

      {/* RECOMMENDED PATH OVERLAY */}
      <div className="absolute bottom-6 left-6 max-w-[280px] pointer-events-auto">
        <div className="liquid-glass border border-white/5 rounded-2xl p-4 overflow-hidden">
            <div className="text-[10px] font-bold tracking-[0.2em] uppercase text-white/20 mb-3 flex items-center gap-2">
                <Target size={12} /> Recommended Path
            </div>
            <div className="space-y-3">
                <LearningPathList userId={userId} />
            </div>
        </div>
      </div>
    </div>
  )
}

function LearningPathList({ userId }) {
    const [paths, setPaths] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        axios.get('/api/v1/lms/learning-paths', { params: { user_id: userId } })
            .then(res => setPaths(res.data.recommendations))
            .finally(() => setLoading(false))
    }, [userId])

    if (loading) return <div className="text-[10px] text-white/10 italic">Calculating trajectory...</div>

    return paths.map((p, i) => (
        <div key={i} className="flex flex-col gap-1 p-2 rounded-xl bg-white/[0.03] border border-white/5 transition-all hover:bg-white/5 cursor-help">
            <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-white/80">{p.concept_name}</span>
                <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${p.priority === 'high' ? 'bg-red-500/20 text-red-400' : 'bg-white/10 text-white/40'}`}>
                    {p.current_mastery}%
                </span>
            </div>
            <p className="text-[9px] text-white/40 italic leading-tight">{p.suggested_action}</p>
        </div>
    ))
}

