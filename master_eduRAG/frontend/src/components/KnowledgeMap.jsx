import { useEffect, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { Info, Orbit, Sparkles, Target, Zap } from 'lucide-react'

const PROCESSING_GRAPH_STATUS = 'processing_graph'

function buildLinks(nodes) {
  const links = []

  for (let i = 0; i < nodes.length - 1; i += 1) {
    const current = nodes[i]
    const next = nodes[i + 1]

    if (current.community != null && current.community === next.community) {
      links.push({ source: current.id, target: next.id })
    } else if (i % 2 === 0) {
      links.push({ source: current.id, target: next.id })
    }
  }

  return links
}

function buildEntityGraph(entities) {
  const nodes = entities.map((ent, idx) => ({
    id: ent.name || `entity-${idx}`,
    name: ent.name || 'Unknown',
    val: 10 + ((ent.mastery ?? 0) * 10),
    mastery: ent.mastery ?? 0,
    type: ent.type || 'concept',
    community: ent.community ?? 0,
    source: 'graph',
  }))

  return { nodes, links: buildLinks(nodes) }
}

function buildConceptFallback(concepts) {
  const nodes = concepts.map((concept, idx) => ({
    id: concept.name || `concept-${idx}`,
    name: concept.name || 'Unknown',
    val: concept.importance === 'high' ? 18 : 14,
    mastery: concept.importance === 'high' ? 0.7 : 0.5,
    type: 'stage_one_concept',
    community: idx % 3,
    source: 'stage_one',
  }))

  return { nodes, links: buildLinks(nodes) }
}

function normalizeText(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

function getLinkNodeId(endpoint) {
  if (!endpoint) {
    return null
  }

  return typeof endpoint === 'object' ? endpoint.id : endpoint
}

function truncateText(value, maxLength = 180) {
  if (!value) {
    return ''
  }

  const cleanValue = String(value).replace(/\s+/g, ' ').trim()
  if (cleanValue.length <= maxLength) {
    return cleanValue
  }

  return `${cleanValue.slice(0, maxLength - 1).trimEnd()}…`
}

function findRelevantSummary(node, summaryContent = '') {
  if (!summaryContent) {
    return ''
  }

  const normalizedNodeName = normalizeText(node?.name)
  const sentences = String(summaryContent)
    .split(/(?<=[.!?])\s+|\n+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean)

  const matchedSentence = sentences.find((sentence) =>
    normalizeText(sentence).includes(normalizedNodeName)
  )

  return truncateText(matchedSentence || sentences[0] || summaryContent)
}

function buildNodeExplainer(node, graphData, artifact) {
  const concepts = artifact?.study_package?.data?.concepts || []
  const summaryContent = artifact?.study_package?.data?.summary?.content || ''
  const normalizedNodeName = normalizeText(node?.name)
  const matchedConcept = concepts.find((concept) => normalizeText(concept?.name) === normalizedNodeName)

  const directConnections = graphData.links
    .map((link) => {
      const sourceId = getLinkNodeId(link.source)
      const targetId = getLinkNodeId(link.target)

      if (sourceId === node.id) {
        return graphData.nodes.find((candidate) => candidate.id === targetId) || null
      }

      if (targetId === node.id) {
        return graphData.nodes.find((candidate) => candidate.id === sourceId) || null
      }

      return null
    })
    .filter(Boolean)
    .filter((candidate, index, collection) => (
      collection.findIndex((entry) => entry.id === candidate.id) === index
    ))

  const communityConnections = graphData.nodes
    .filter((candidate) => candidate.id !== node.id && candidate.community === node.community)
    .filter((candidate, index, collection) => (
      collection.findIndex((entry) => entry.id === candidate.id) === index
    ))

  const visibleConnections = (directConnections.length > 0 ? directConnections : communityConnections).slice(0, 4)
  const summary =
    truncateText(matchedConcept?.definition, 200) ||
    findRelevantSummary(node, summaryContent) ||
    `This ${node.type || 'concept'} sits in community ${node.community ?? 0} with ${(visibleConnections.length || 0)} nearby connection${visibleConnections.length === 1 ? '' : 's'} in the current map.`

  return {
    summary,
    connections: visibleConnections,
    connectionLabel: directConnections.length > 0 ? 'Direct connections' : 'Same cluster',
  }
}

export default function KnowledgeMap({ userId, uploadId, artifact }) {
  const [data, setData] = useState({ nodes: [], links: [] })
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState(null)
  const [graphMeta, setGraphMeta] = useState({
    status: artifact?.processing_status || artifact?.study_package?.status || PROCESSING_GRAPH_STATUS,
    isGraphReady: Boolean(artifact?.is_graph_ready),
    triplesCount: artifact?.study_package?.graph_metadata?.triples_count || 0,
    mode: 'empty',
  })
  const fgRef = useRef()

  useEffect(() => {
    let isActive = true

    const refreshGraph = async ({ silent = false } = {}) => {
      if (!silent) {
        setLoading(true)
      }

      try {
        const [artifactRes, graphViewRes, entityRes] = await Promise.allSettled([
          axios.get(`/api/v1/uploads/${uploadId}`),
          axios.get(`/api/v1/graph/view/${uploadId}`),
          axios.get('/api/v1/graph/entities', { params: { upload_id: uploadId } }),
        ])

        if (!isActive) {
          return
        }

        const latestArtifact = artifactRes.status === 'fulfilled' ? artifactRes.value.data : artifact
        const graphView = graphViewRes.status === 'fulfilled' ? graphViewRes.value.data : null
        const entities = entityRes.status === 'fulfilled' ? entityRes.value.data : []
        const concepts = latestArtifact?.study_package?.data?.concepts || []

        let graphData = { nodes: [], links: [] }
        let mode = 'empty'

        if (entities.length > 0) {
          graphData = buildEntityGraph(entities)
          mode = 'graph'
        } else if (concepts.length > 0) {
          graphData = buildConceptFallback(concepts)
          mode = 'stage_one'
        }

        setData(graphData)
        setSelectedNode((current) => {
          if (!current) {
            return null
          }
          return graphData.nodes.find((node) => node.id === current.id) || null
        })

        setGraphMeta({
          status:
            graphView?.status ||
            latestArtifact?.processing_status ||
            latestArtifact?.study_package?.status ||
            PROCESSING_GRAPH_STATUS,
          isGraphReady: Boolean(
            graphView?.is_graph_ready ??
            latestArtifact?.is_graph_ready ??
            latestArtifact?.study_package?.graph_metadata?.graph_path
          ),
          triplesCount:
            graphView?.triples_count ||
            latestArtifact?.study_package?.graph_metadata?.triples_count ||
            0,
          mode,
        })
      } catch (err) {
        if (!isActive) {
          return
        }
        console.error('Failed to fetch graph', err)
        setGraphMeta((current) => ({ ...current, mode: 'empty' }))
      } finally {
        if (isActive) {
          setLoading(false)
        }
      }
    }

    refreshGraph()

    return () => {
      isActive = false
    }
  }, [artifact, uploadId, userId])

  useEffect(() => {
    if (graphMeta.status !== PROCESSING_GRAPH_STATUS || graphMeta.isGraphReady) {
      return undefined
    }

    const intervalId = window.setInterval(async () => {
      try {
        const [graphViewRes, entityRes] = await Promise.allSettled([
          axios.get(`/api/v1/graph/view/${uploadId}`),
          axios.get('/api/v1/graph/entities', { params: { upload_id: uploadId } }),
        ])

        const graphView = graphViewRes.status === 'fulfilled' ? graphViewRes.value.data : null
        const entities = entityRes.status === 'fulfilled' ? entityRes.value.data : []

        if (entities.length > 0) {
          setData(buildEntityGraph(entities))
        }

        setGraphMeta((current) => ({
          ...current,
          status: graphView?.status || current.status,
          isGraphReady: Boolean(graphView?.is_graph_ready || entities.length > 0),
          triplesCount: graphView?.triples_count || current.triplesCount,
          mode: entities.length > 0 ? 'graph' : current.mode,
        }))
      } catch (err) {
        console.error('Failed to refresh graph status', err)
      }
    }, 5000)

    return () => window.clearInterval(intervalId)
  }, [graphMeta.isGraphReady, graphMeta.status, uploadId])

  const getMasteryColor = (mastery) => {
    if (mastery >= 0.8) return '#10b981'
    if (mastery >= 0.5) return '#f59e0b'
    return '#ef4444'
  }

  const handleNodeClick = (node) => {
    setSelectedNode(node)
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 400)
      fgRef.current.zoom(2.5, 400)
    }
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-black/40 rounded-[2.5rem] backdrop-blur-xl">
        <div className="animate-pulse text-white/40 tracking-widest uppercase text-xs font-bold font-poppins">
          Synchronizing Cognitive Topology...
        </div>
      </div>
    )
  }

  const showStageOneFallback = graphMeta.mode === 'stage_one'
  const showEmptyState = data.nodes.length === 0
  const selectedNodeExplainer = selectedNode
    ? buildNodeExplainer(selectedNode, data, artifact)
    : null

  return (
    <div className="relative w-full h-full bg-black/20 rounded-[2.5rem] overflow-hidden border border-white/5 shadow-2xl">
      {!showEmptyState && (
        <ForceGraph2D
          ref={fgRef}
          graphData={data}
          nodeLabel="name"
          nodeVal={(node) => node.val}
          nodeColor={(node) => getMasteryColor(node.mastery)}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name
            const fontSize = 12 / globalScale
            ctx.font = `${fontSize}px Inter`
            const textWidth = ctx.measureText(label).width
            const background = [textWidth, fontSize].map((value) => value + fontSize * 0.2)
            const radius = Math.max(4, (node.val || 10) / 4)

            ctx.shadowBlur = 15
            ctx.shadowColor = getMasteryColor(node.mastery)
            ctx.fillStyle = getMasteryColor(node.mastery)
            ctx.beginPath()
            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false)
            ctx.fill()
            ctx.shadowBlur = 0

            if (globalScale > 1.5) {
              ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
              ctx.fillRect(node.x - background[0] / 2, node.y - background[1] / 2 - 10, ...background)
              ctx.textAlign = 'center'
              ctx.textBaseline = 'middle'
              ctx.fillStyle = 'white'
              ctx.fillText(label, node.x, node.y - 10)
            }
          }}
          linkColor={() => 'rgba(255,255,255,0.08)'}
          linkWidth={1}
          onNodeClick={handleNodeClick}
          cooldownTicks={100}
        />
      )}

      {showEmptyState && (
        <div className="absolute inset-0 flex items-center justify-center p-8">
          <div className="max-w-md text-center liquid-glass rounded-[2rem] border border-white/10 p-8">
            <div className="w-14 h-14 mx-auto rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-5">
              <Info size={22} className="text-white/50" />
            </div>
            <h3 className="text-xl font-medium tracking-tight mb-3">Graph Not Ready Yet</h3>
            <p className="text-sm text-white/45 leading-relaxed">
              {graphMeta.status === PROCESSING_GRAPH_STATUS
                ? 'Stage 1 is complete. Stage 2 is still grounding the deep connection graph, so the live topology is not available yet.'
                : 'No graph entities were found for this artifact yet. Try reopening the artifact after processing completes.'}
            </p>
          </div>
        </div>
      )}

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
              <Info size={18} />
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

              <div className="p-4 bg-white/10 border border-white/5 rounded-2xl space-y-4">
                <div>
                  <div className="text-[10px] font-bold tracking-[0.2em] uppercase text-white/30 mb-2 flex items-center gap-2">
                    <Sparkles size={12} />
                    Mini Explainer
                  </div>
                  <p className="text-sm text-white/60 leading-relaxed">
                    {selectedNodeExplainer?.summary}
                  </p>
                </div>

                <div>
                  <div className="text-[10px] font-bold tracking-[0.2em] uppercase text-white/30 mb-2">
                    {selectedNodeExplainer?.connectionLabel || 'Connections'}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(selectedNodeExplainer?.connections || []).length > 0 ? (
                      selectedNodeExplainer.connections.map((connection) => (
                        <button
                          key={connection.id}
                          type="button"
                          onClick={() => handleNodeClick(connection)}
                          className="px-2.5 py-1 rounded-full bg-white/8 border border-white/10 text-[10px] font-semibold text-white/75 hover:bg-white/12 transition-colors"
                        >
                          {connection.name}
                        </button>
                      ))
                    ) : (
                      <span className="text-xs text-white/35">
                        No nearby connections have been mapped for this node yet.
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-white/25">
                  <span>{selectedNode.type || 'Cognitive Node'}</span>
                  <span>•</span>
                  <span>Community {selectedNode.community ?? 0}</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="absolute top-6 left-6 pointer-events-none">
        <h4 className="text-xs font-bold tracking-[0.3em] uppercase text-white/30 flex items-center gap-2">
          <Zap size={14} className={graphMeta.status === PROCESSING_GRAPH_STATUS ? 'animate-pulse' : ''} />
          Cognitive Topology
        </h4>
        <div className="text-[10px] font-medium text-white/20 mt-1 uppercase tracking-widest">
          {data.nodes.length} Neural Intersections
        </div>
      </div>

      <div className="absolute top-6 right-6 pointer-events-none">
        <div className="px-3 py-2 rounded-2xl bg-white/5 border border-white/10 text-[10px] font-bold tracking-[0.2em] uppercase text-white/50 flex items-center gap-2">
          <Orbit size={12} className={graphMeta.status === PROCESSING_GRAPH_STATUS ? 'animate-spin' : ''} />
          {graphMeta.status === PROCESSING_GRAPH_STATUS
            ? 'Deep Graph Processing'
            : showStageOneFallback
              ? 'Stage 1 Concept View'
              : 'Graph Grounded'}
        </div>
      </div>

      {showStageOneFallback && !showEmptyState && (
        <div className="absolute inset-x-6 bottom-28 pointer-events-none">
          <div className="max-w-md liquid-glass border border-white/10 rounded-2xl p-4 text-xs text-white/50 leading-relaxed">
            Stage 1 concepts are shown now so the topology tab is never empty. The deeper graph will replace this view automatically when Stage 2 grounding completes.
          </div>
        </div>
      )}

      {!showEmptyState && graphMeta.triplesCount > 0 && (
        <div className="absolute top-16 left-6 pointer-events-none text-[10px] font-medium text-white/20 uppercase tracking-widest">
          {graphMeta.triplesCount} knowledge triples
        </div>
      )}

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
      .then((res) => setPaths(res.data.recommendations || []))
      .finally(() => setLoading(false))
  }, [userId])

  if (loading) {
    return <div className="text-[10px] text-white/10 italic">Calculating trajectory...</div>
  }

  if (paths.length === 0) {
    return <div className="text-[10px] text-white/20 italic">No priority remediation path right now.</div>
  }

  return paths.map((path, index) => (
    <div
      key={`${path.concept_id || path.concept_name || 'path'}-${index}`}
      className="flex flex-col gap-1 p-2 rounded-xl bg-white/[0.03] border border-white/5 transition-all hover:bg-white/5 cursor-help"
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold text-white/80">{path.concept_name}</span>
        <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${path.priority === 'high' ? 'bg-red-500/20 text-red-400' : 'bg-white/10 text-white/40'}`}>
          {path.current_mastery}%
        </span>
      </div>
      <p className="text-[9px] text-white/40 italic leading-tight">{path.suggested_action}</p>
    </div>
  ))
}
