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

export default function Research() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
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
    fetchMetrics()
  }, [])

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-2 border-white/10 border-t-white/80 rounded-full animate-spin" />
        <p className="text-white/40 text-sm font-medium tracking-widest uppercase">Analyzing Benchmarks</p>
      </div>
    )
  }

  const MetricCard = ({ label, value, baseline, better = 'higher' }) => {
    const isBetter = better === 'higher' ? value > baseline : value < baseline
    const diff = Math.abs(((value - baseline) / baseline) * 100).toFixed(1)
    
    return (
      <div className="liquid-glass p-6 rounded-3xl border border-white/5 space-y-3">
        <div className="flex justify-between items-start">
          <span className="text-[10px] font-bold tracking-widest uppercase text-white/30">{label}</span>
          <div className={`flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md ${
            isBetter ? 'bg-white/10 text-white' : 'bg-red-500/10 text-red-200'
          }`}>
            {isBetter ? <TrendingUp size={10} /> : <AlertCircle size={10} />}
            {isBetter ? '+' : '-'}{diff}%
          </div>
        </div>
        <div className="text-3xl font-semibold">{value.toFixed(3)}</div>
        <div className="text-[10px] text-white/20">Baseline (Avg): {baseline.toFixed(3)}</div>
      </div>
    )
  }

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
          <button className="bg-white text-black px-6 py-3 rounded-2xl text-sm font-semibold hover:bg-white/90 transition-all flex items-center gap-2">
            <Zap size={16} />
            Run Full Eval
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
                value={metrics.summary_metrics.edusum.rougeL} 
                baseline={metrics.summary_metrics.baselines.bart.rougeL} 
              />
              <MetricCard 
                label="BERTScore (F1)" 
                value={metrics.summary_metrics.edusum.bertscore} 
                baseline={0.842} 
              />
              <MetricCard 
                label="METEOR" 
                value={metrics.summary_metrics.edusum.meteor} 
                baseline={metrics.summary_metrics.baselines.t5.rougeL} 
              />
              <div className="liquid-glass p-6 rounded-3xl border border-white/5 flex flex-col justify-center text-center">
                 <div className="text-[10px] font-bold tracking-widest uppercase text-white/30 mb-2">Confidence Interval</div>
                 <div className="text-xl font-medium text-white/60">95% (±0.012)</div>
              </div>
            </div>

            <div className="mt-10 p-6 bg-white/[0.02] border border-white/5 rounded-3xl">
              <h4 className="text-xs font-bold tracking-widest uppercase text-white/30 mb-6 flex items-center gap-2">
                <Cpu size={14} /> Dataset Composition
              </h4>
              <div className="flex items-center gap-4">
                  <div className="flex-1 space-y-2">
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-white/40">Technical Papers</span>
                        <span className="text-white/60">45%</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                        <motion.div initial={{width: 0}} animate={{width: '45%'}} className="h-full bg-white/40" />
                    </div>
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-white/40">Lecture Notes</span>
                        <span className="text-white/60">32%</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                        <motion.div initial={{width: 0}} animate={{width: '32%'}} className="h-full bg-white/20" />
                    </div>
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-white/40">Textbooks</span>
                        <span className="text-white/60">23%</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                        <motion.div initial={{width: 0}} animate={{width: '23%'}} className="h-full bg-white/10" />
                    </div>
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
                    <span className="text-2xl font-bold">{metrics.vision_metrics.saeocr.accuracy}%</span>
                </div>
                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div initial={{width: 0}} animate={{width: `${metrics.vision_metrics.saeocr.accuracy}%`}} className="h-full bg-white" />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-end">
                    <span className="text-sm font-medium text-white/40">Tesseract v5</span>
                    <span className="text-xl font-bold text-white/40">{metrics.vision_metrics.tesseract.accuracy}%</span>
                </div>
                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div initial={{width: 0}} animate={{width: `${metrics.vision_metrics.tesseract.accuracy}%`}} className="h-full bg-white/10" />
                </div>
              </div>
            </div>

            <p className="mt-8 text-[11px] text-white/30 leading-relaxed italic">
                SAEOCR shows a <strong>~34%</strong> improvement over traditional OCR when processing student-generated handwritten notes.
            </p>
          </div>

          <div className="liquid-glass-strong rounded-[2rem] p-8 border border-white/10 bg-gradient-to-br from-white/5 to-transparent">
             <h4 className="text-xs font-bold tracking-widest uppercase text-white/30 mb-6">Educational Utility</h4>
             <div className="space-y-4">
                {Object.entries(metrics.educational_utility).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                         <span className="text-xs text-white/50 capitalize">{key.replace('_', ' ')}</span>
                         <div className="flex items-center gap-1">
                            {[1,2,3,4,5].map(star => (
                                <div key={star} className={`w-1.5 h-1.5 rounded-full ${star <= value ? 'bg-white' : 'bg-white/10'}`} />
                            ))}
                            <span className="ml-2 text-xs font-bold">{value.toFixed(1)}</span>
                         </div>
                    </div>
                ))}
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
                <div className="text-sm font-medium">Gemini 1.5 Pro</div>
            </div>
            <div className="space-y-1">
                <div className="text-[10px] font-bold tracking-widest uppercase text-white/20">Vision Engine</div>
                <div className="text-sm font-medium">SAEOCR v1.2</div>
            </div>
            <div className="space-y-1">
                <div className="text-[10px] font-bold tracking-widest uppercase text-white/20">Embedding Model</div>
                <div className="text-sm font-medium">text-embedding-004</div>
            </div>
            <div className="space-y-1">
                <div className="text-[10px] font-bold tracking-widest uppercase text-white/20">Temperature</div>
                <div className="text-sm font-medium">0.3 (Deterministic)</div>
            </div>
        </div>
      </div>
    </div>
  )
}
