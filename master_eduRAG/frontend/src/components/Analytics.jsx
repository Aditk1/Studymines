import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, Users, Brain, AlertTriangle, ArrowLeft } from 'lucide-react'

export default function Analytics({ user, onBack }) {
  const [heatmapData, setHeatmapData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulated fetching from /api/v1/lms/analytics/teacher/insight
    setTimeout(() => {
      setHeatmapData([
        { concept: 'Schrödinger Equation', struggle_index: 85, mentions: 134, confidence: 0.92 },
        { concept: 'Heisenberg Uncertainty', struggle_index: 60, mentions: 89, confidence: 0.88 },
        { concept: 'Wave Function Collapse', struggle_index: 20, mentions: 45, confidence: 0.95 },
        { concept: 'Quantum Entanglement', struggle_index: 92, mentions: 210, confidence: 0.82 },
        { concept: 'Gradient Descent', struggle_index: 45, mentions: 78, confidence: 0.91 },
      ])
      setLoading(false)
    }, 800)
  }, [])

  return (
    <div className="h-full flex flex-col p-2 space-y-6 overflow-y-auto custom-scrollbar">
      <header className="flex items-center gap-4 mb-4">
        {onBack && (
          <button 
            onClick={onBack}
            className="w-10 h-10 rounded-full liquid-glass flex items-center justify-center hover:bg-white/10 transition-colors"
          >
            <ArrowLeft size={18} />
          </button>
        )}
        <div>
          <h2 className="text-3xl font-medium tracking-tighter">Curriculum <em className="text-white/60">Analytics</em></h2>
          <p className="text-sm text-white/40 mt-1">Cognitive Heatmap & Global Mastery Insights</p>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* KPI Cards */}
        <div className="liquid-glass rounded-3xl p-6 border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-white/40 text-sm font-medium">
            <span>Graph Concepts Monitored</span>
            <Brain size={16} />
          </div>
          <div className="text-4xl font-semibold">1,402</div>
          <div className="text-xs text-green-400 font-medium">+124 this week</div>
        </div>

        <div className="liquid-glass rounded-3xl p-6 border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-white/40 text-sm font-medium">
            <span>Global Knowledge Mastery</span>
            <TrendingUp size={16} />
          </div>
          <div className="text-4xl font-semibold">68.4%</div>
          <div className="text-xs text-orange-400 font-medium">-2.1% from last month</div>
        </div>

        <div className="liquid-glass rounded-3xl p-6 border border-white/5 space-y-2 bg-red-500/5">
          <div className="flex items-center justify-between text-red-300 text-sm font-medium">
            <span>High-Struggle Concepts</span>
            <AlertTriangle size={16} />
          </div>
          <div className="text-4xl font-semibold text-red-100">2</div>
          <div className="text-xs text-red-400 font-medium">Requires clarification in lecture</div>
        </div>
      </div>

      <div className="liquid-glass-strong rounded-[2rem] p-8 border border-white/5 flex-1 flex flex-col">
        <h3 className="text-xl font-medium mb-6 flex items-center gap-2">
          <Brain size={20} className="text-white/60" />
          Teacher's Insight: Concept Heatmap
        </h3>

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 overflow-x-auto gap-4">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead>
                <tr className="text-white/40 font-medium border-b border-white/10">
                  <th className="pb-3 pl-4">Graph Entity / Concept</th>
                  <th className="pb-3 text-right">Student Queries</th>
                  <th className="pb-3 text-right">Extraction Confidence</th>
                  <th className="pb-3 text-right pr-4">Struggle Index</th>
                </tr>
              </thead>
              <tbody>
                {heatmapData.sort((a,b) => b.struggle_index - a.struggle_index).map((data, idx) => (
                  <motion.tr 
                    key={idx}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="py-4 pl-4 font-medium tracking-tight">{data.concept}</td>
                    <td className="py-4 text-right text-white/60">{data.mentions}</td>
                    <td className="py-4 text-right text-white/60">{Math.round(data.confidence * 100)}%</td>
                    <td className="py-4 pr-4">
                      <div className="flex justify-end items-center gap-3">
                        <span className={`font-bold ${data.struggle_index > 80 ? 'text-red-400' : data.struggle_index > 50 ? 'text-orange-400' : 'text-green-400'}`}>
                          {data.struggle_index.toFixed(1)} / 100
                        </span>
                        <div className="w-24 h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${data.struggle_index > 80 ? 'bg-red-500' : data.struggle_index > 50 ? 'bg-orange-500' : 'bg-green-500'}`}
                            style={{ width: `${data.struggle_index}%` }}
                          />
                        </div>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  )
}
