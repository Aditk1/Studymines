/**
 * Research metrics and benchmark visibility page.
 */
import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import { 
  Beaker, 
  BarChart2, 
  Search, 
  Zap, 
  FileJson, 
  Download,
  AlertCircle,
  TrendingUp,
  Cpu
} from 'lucide-react'

/**
 * Research metrics and benchmark visibility page.
 */
export default function Research() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isEvaluating, setIsEvaluating] = useState(false)

  const fetchMetrics = async () => {
    try {
      const response = await axios.get('/api/v1/research/metrics')
      setMetrics(response.data)
    } catch (err) {
      console.error("Failed to fetch research metrics", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMetrics()
  }, [])

  const handleRunEval = async () => {
    setIsEvaluating(true)
    try {
      await axios.post('/api/v1/research/eval/run')
      await fetchMetrics()
    } catch (err) {
      console.error("Failed to run evaluation", err)
    } finally {
      setIsEvaluating(false)
    }
  }

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-2 border-white/10 border-t-white/80 rounded-full animate-spin" />
        <p className="text-white/40 text-sm font-medium tracking-widest uppercase">Analyzing Benchmarks</p>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4 text-center">
        <AlertCircle size={48} className="text-red-500/40" />
        <div>
          <h3 className="text-xl font-medium">Metrics Unavailable</h3>
          <p className="text-white/30 text-sm italic">Failed to connect to research benchmarks.</p>
        </div>
      </div>
    )
  }

  const formatMetric = (value, suffix = '') => (
    typeof value === 'number' ? `${value.toFixed(3)}${suffix}` : 'N/A'
  )

  const MetricCard = ({ label, value, baseline, better = 'higher', note = 'No verified benchmark available in the current repo snapshot.' }) => {
    const hasValue = typeof value === 'number'
    const hasBaseline = typeof baseline === 'number' && baseline !== 0
    const isComparable = hasValue && hasBaseline
    const isBetter = isComparable ? (better === 'higher' ? value > baseline : value < baseline) : null
    const diff = isComparable ? Math.abs(((value - baseline) / baseline) * 100).toFixed(1) : null
    
    return (
      <div className="liquid-glass p-6 rounded-3xl border border-white/5 space-y-3">
        <div className="flex justify-between items-start">
          <span className="text-[10px] font-bold tracking-widest uppercase text-white/30">{label}</span>
          {isComparable ? (
            <div className={`flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md ${
              isBetter ? 'bg-white/10 text-white' : 'bg-red-500/10 text-red-200'
            }`}>
              {isBetter ? <TrendingUp size={10} /> : <AlertCircle size={10} />}
              {isBetter ? '+' : '-'}{diff}%
            </div>
          ) : (
            <div className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md bg-white/5 text-white/40">
              <AlertCircle size={10} />
              Pending
            </div>
          )}
        </div>
        <div className="text-3xl font-semibold">{formatMetric(value)}</div>
        <div className="text-[10px] text-white/20">
          {hasBaseline ? `Baseline (Avg): ${baseline.toFixed(3)}` : note}
        </div>
      </div>
    )
  }

  const summaryMetrics = metrics?.summary_metrics?.edusum || {}
  const baselines = metrics?.summary_metrics?.baselines || {}
  const graphAggregate = metrics?.graph_metrics?.aggregate || {}
  const graphPrimary = metrics?.graph_metrics?.primary_graph || null
  const visionMetrics = metrics?.vision_metrics || {}
  const liveConfig = metrics?.metadata?.system_config || {}
  const dbSnapshot = metrics?.metadata?.db || {}

  return (
    <div className="max-w-6xl mx-auto py-4 space-y-10">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h2 className="text-5xl font-medium tracking-tighter mb-2">Research <em className="text-white/60">Center</em></h2>
          <p className="text-white/40 text-lg">Empirical benchmarks and system performance analytics.</p>
        </div>
        <div className="flex gap-3">
          <button className="liquid-glass px-6 py-3 rounded-2xl text-sm font-medium hover:bg-white/5 transition-all text-white/70 flex items-center gap-2">
            <Download size={16} />
            Export BibTeX
          </button>
          <button 
            onClick={handleRunEval}
            disabled={isEvaluating}
            className={`px-6 py-3 rounded-2xl text-sm font-semibold transition-all flex items-center gap-2 ${
              isEvaluating 
                ? 'bg-white/20 text-white cursor-not-allowed' 
                : 'bg-white text-black hover:bg-white/90'
            }`}
          >
            {isEvaluating ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                Evaluating...
              </>
            ) : (
              <>
                <Zap size={16} />
                Run Full Eval
              </>
            )}
          </button>
        </div>
      </header>

      {/* OVERVIEW STATS */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* SUMMARIZATION PERFORMANCE */}
        <div className="lg:col-span-8 liquid-glass-strong rounded-[2.5rem] p-10 relative overflow-hidden">
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center text-white">
                <BarChart2 size={20} />
              </div>
              <h3 className="text-2xl font-medium tracking-tighter">Summarization Benchmarks <em className="text-white/40 text-sm">(Approach 1)</em></h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <MetricCard 
                label="ROUGE-L (F1)" 
                value={summaryMetrics.rougeL} 
                baseline={baselines?.bart?.rougeL} 
                note={summaryMetrics.note}
              />
              <MetricCard 
                label="BERTScore (F1)" 
                value={summaryMetrics.bertscore} 
                baseline={null} 
                note={summaryMetrics.note}
              />
              <MetricCard 
                label="METEOR" 
                value={summaryMetrics.meteor} 
                baseline={baselines?.t5?.meteor} 
                note={summaryMetrics.note}
              />
              <div className="liquid-glass p-6 rounded-3xl border border-white/5 flex flex-col justify-center text-center">
                 <div className="text-[10px] font-bold tracking-widest uppercase text-white/30 mb-2">Evaluation Status</div>
                 <div className="text-xl font-medium text-white/60">
                   {summaryMetrics.status === 'unavailable' ? 'Awaiting Gold Set' : 'Computed'}
                 </div>
              </div>
            </div>

            <div className="mt-10 p-6 bg-white/[0.02] border border-white/5 rounded-3xl">
              <h4 className="text-xs font-bold tracking-widest uppercase text-white/30 mb-6 flex items-center gap-2">
                <Cpu size={14} /> Live Project Snapshot
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="liquid-glass rounded-2xl p-4">
                    <div className="text-[10px] font-bold tracking-widest uppercase text-white/25 mb-2">Uploads</div>
                    <div className="text-2xl font-semibold">{dbSnapshot.uploads_total ?? 0}</div>
                    <div className="text-white/35 text-xs">Summaries: {dbSnapshot.uploads_with_summary ?? 0}</div>
                  </div>
                  <div className="liquid-glass rounded-2xl p-4">
                    <div className="text-[10px] font-bold tracking-widest uppercase text-white/25 mb-2">Graph Artifacts</div>
                    <div className="text-2xl font-semibold">{graphAggregate.graph_artifacts ?? 0}</div>
                    <div className="text-white/35 text-xs">Graph-ready uploads: {dbSnapshot.uploads_with_graph ?? 0}</div>
                  </div>
                  <div className="liquid-glass rounded-2xl p-4">
                    <div className="text-[10px] font-bold tracking-widest uppercase text-white/25 mb-2">Primary Graph</div>
                    <div className="text-lg font-semibold">{graphPrimary?.nodes ?? 'N/A'} nodes</div>
                    <div className="text-white/35 text-xs">{graphPrimary?.artifact || 'No graph artifact detected'}</div>
                  </div>
              </div>
            </div>
          </div>
          <div className="absolute top-0 right-0 w-80 h-80 bg-white/5 blur-[120px] pointer-events-none" />
        </div>

        {/* VISION PERFORMANCE */}
        <div className="lg:col-span-4 space-y-6">
          <div className="liquid-glass rounded-[2rem] p-8 group">
            <h4 className="text-xs font-bold tracking-widest uppercase text-white/30 mb-8 flex items-center justify-between">
                Vision Accuracy <em className="text-white/10">(SAEOCR)</em>
                <Zap size={14} className="text-white/40" />
            </h4>
            
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between items-end">
                    <span className="text-sm font-medium">SAEOCR Accuracy</span>
                    <span className="text-2xl font-bold">
                      {typeof visionMetrics?.saeocr?.accuracy === 'number' ? `${visionMetrics.saeocr.accuracy}%` : 'N/A'}
                    </span>
                </div>
                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div initial={{width: 0}} animate={{width: `${visionMetrics?.saeocr?.accuracy || 0}%`}} className="h-full bg-white" />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-end">
                    <span className="text-sm font-medium text-white/40">Tesseract v5</span>
                    <span className="text-xl font-bold text-white/40">
                      {typeof visionMetrics?.tesseract?.accuracy === 'number' ? `${visionMetrics.tesseract.accuracy}%` : 'N/A'}
                    </span>
                </div>
                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div initial={{width: 0}} animate={{width: `${visionMetrics?.tesseract?.accuracy || 0}%`}} className="h-full bg-white/10" />
                </div>
              </div>
            </div>

            <p className="mt-8 text-[11px] text-white/30 leading-relaxed italic">
                {visionMetrics?.note || 'No verified OCR benchmark logs are currently available in the repo snapshot.'}
            </p>
          </div>

          <div className="liquid-glass-strong rounded-[2rem] p-8 border border-white/10 bg-gradient-to-br from-white/5 to-transparent">
             <h4 className="text-xs font-bold tracking-widest uppercase text-white/30 mb-6">Educational Utility</h4>
             <div className="space-y-4">
                {Object.entries(metrics?.educational_utility || {}).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                         <span className="text-xs text-white/50 capitalize">{key.replace('_', ' ')}</span>
                         <div className="flex items-center gap-1">
                            {[1,2,3,4,5].map(star => (
                                <div key={star} className={`w-1.5 h-1.5 rounded-full ${star <= value ? 'bg-white' : 'bg-white/10'}`} />
                            ))}
                            <span className="ml-2 text-xs font-bold">{value?.toFixed(1) || '0.0'}</span>
                         </div>
                    </div>
                ))}
                {(!metrics?.educational_utility || Object.keys(metrics.educational_utility).length === 0) && (
                    <div className="text-white/20 text-xs italic">No utility benchmarks available</div>
                )}
             </div>
          </div>
        </div>
      </div>

      {/* PUBLICATIONS / CITATIONS SHELF */}
      <div className="liquid-glass rounded-[2.5rem] p-10">
        <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 liquid-glass rounded-xl flex items-center justify-center text-white/40">
                <FileJson size={20} />
            </div>
            <h3 className="text-2xl font-medium tracking-tighter">System <em className="text-white/40">Hyperparameters</em></h3>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="space-y-1">
                <div className="text-[10px] font-bold tracking-widest uppercase text-white/20">LLM Engine</div>
                <div className="text-sm font-medium">{liveConfig.llm_provider || 'N/A'} / {liveConfig.llm_model || 'N/A'}</div>
            </div>
            <div className="space-y-1">
                <div className="text-[10px] font-bold tracking-widest uppercase text-white/20">Vision Engine</div>
                <div className="text-sm font-medium">Image preprocessing + extractor pipeline</div>
            </div>
            <div className="space-y-1">
                <div className="text-[10px] font-bold tracking-widest uppercase text-white/20">Embedding Model</div>
                <div className="text-sm font-medium">{liveConfig.embedding_model || 'N/A'}</div>
            </div>
            <div className="space-y-1">
                <div className="text-[10px] font-bold tracking-widest uppercase text-white/20">Temperature</div>
                <div className="text-sm font-medium">{typeof liveConfig.temperature === 'number' ? `${liveConfig.temperature} (Configured)` : 'N/A'}</div>
            </div>
        </div>
      </div>
    </div>
  )
}
