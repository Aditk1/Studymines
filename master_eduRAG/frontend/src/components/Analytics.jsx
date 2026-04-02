import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, Users, Brain, AlertTriangle, ArrowLeft } from 'lucide-react'
import axios from 'axios'

import { useSearchParams } from 'react-router-dom'

export default function Analytics({ user, onBack }) {
  const [searchParams] = useSearchParams()
  const filterUserId = searchParams.get('user_id')
  
  const [heatmapData, setHeatmapData] = useState([])
  const [riskData, setRiskData] = useState([])
  const [kpiData, setKpiData] = useState({ concepts_monitored: 0, global_mastery_pct: 0, high_struggle_count: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [heatmapRes, kpiRes, riskRes] = await Promise.all([
            axios.get('/api/v1/lms/stats/heatmap'),
            axios.get('/api/v1/lms/stats/kpis'),
            axios.get('/api/v1/lms/risk-flags')
        ])
        
        setHeatmapData(heatmapRes.data)
        setKpiData(kpiRes.data)
        
        // Filter risk data if user_id is provided
        const allRisks = riskRes.data
        if (filterUserId) {
            setRiskData(allRisks.filter(r => r.student_id === filterUserId))
        } else {
            setRiskData(allRisks)
        }
      } catch (err) {
        console.error("Failed to fetch analytics", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
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
          <h2 className="text-3xl font-medium tracking-tighter">
            {filterUserId ? `Student Performance` : `Curriculum Analytics`}
          </h2>
          <p className="text-sm text-white/40 mt-1">
            {filterUserId ? `Specific Mastery Insights` : `Cognitive Heatmap & Global Mastery Insights`}
          </p>
        </div>
        {filterUserId && (
          <button 
            onClick={() => {
                const url = new URL(window.location.href)
                url.searchParams.delete('user_id')
                window.history.replaceState({}, '', url)
                window.location.reload()
            }}
            className="ml-auto px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-xs font-bold uppercase tracking-widest transition-all"
          >
            Clear Filter
          </button>
        )}
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* KPI Cards */}
        <div className="liquid-glass rounded-3xl p-6 border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-white/40 text-sm font-medium">
            <span>Graph Concepts Monitored</span>
            <Brain size={16} />
          </div>
          <div className="text-4xl font-semibold">{kpiData.concepts_monitored?.toLocaleString()}</div>
          <div className="text-xs text-green-400 font-medium">Auto-extracted from documents</div>
        </div>

        <div className="liquid-glass rounded-3xl p-6 border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-white/40 text-sm font-medium">
            <span>Global Knowledge Mastery</span>
            <TrendingUp size={16} />
          </div>
          <div className="text-4xl font-semibold">{kpiData.global_mastery_pct}%</div>
          <div className="text-xs text-white/40 font-medium tracking-widest uppercase">Target: 85%</div>
        </div>

        <div className="liquid-glass rounded-3xl p-6 border border-white/5 space-y-2 bg-red-500/5">
          <div className="flex items-center justify-between text-red-300 text-sm font-medium">
            <span>High-Struggle Concepts</span>
            <AlertTriangle size={16} />
          </div>
          <div className="text-4xl font-semibold text-red-100">{kpiData.high_struggle_count}</div>
          <div className="text-xs text-red-400 font-medium tracking-widest uppercase">Requires Lecture Focus</div>
        </div>
      </div>

      <div className="liquid-glass-strong rounded-[2rem] p-8 border border-white/5 flex-1 flex flex-col min-h-[400px]">
        <h3 className="text-xl font-medium mb-6 flex items-center gap-2">
          <Brain size={20} className="text-white/60" />
          Concept Heatmap (Weighted Struggle Index)
        </h3>

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 overflow-x-auto gap-4">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead>
                <tr className="text-white/40 font-medium border-b border-white/10 uppercase tracking-widest text-[10px]">
                  <th className="pb-3 pl-4">Graph Entity / Concept</th>
                  <th className="pb-3 text-right">Extracted Mentions</th>
                  <th className="pb-3 text-right">AI Extraction Confidence</th>
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
                    <td className="py-4 pl-4 font-medium tracking-tight truncate max-w-[200px]">{data.concept}</td>
                    <td className="py-4 text-right text-white/60">{data.mentions}</td>
                    <td className="py-4 text-right text-white/60">{Math.round(data.confidence * 100)}%</td>
                    <td className="py-4 pr-4">
                      <div className="flex justify-end items-center gap-3">
                        <span className={`font-bold ${data.struggle_index > 80 ? 'text-red-400' : data.struggle_index > 50 ? 'text-orange-400' : 'text-green-400'}`}>
                          {data.struggle_index.toFixed(1)} / 100
                        </span>
                        <div className="w-32 h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${data.struggle_index > 80 ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : data.struggle_index > 50 ? 'bg-orange-500' : 'bg-green-500'}`}
                            style={{ width: `${data.struggle_index}%` }}
                          />
                        </div>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
            {heatmapData.length === 0 && <div className="py-20 text-center text-white/10 italic">Awaiting document ingestion for graph mapping.</div>}
          </div>
        )}
      </div>

      {/* ACADEMIC RISK REPORT */}
      <div className="liquid-glass rounded-[2rem] p-8 border border-white/5 mb-10">
        <h3 className="text-xl font-medium mb-6 flex items-center gap-2">
          <AlertTriangle size={20} className="text-red-400" />
          Predictive Academic Risk Report
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {riskData.length > 0 ? riskData.map((risk, idx) => (
                <div key={idx} className="p-6 bg-white/[0.03] border border-white/5 rounded-2xl relative overflow-hidden group">
                    <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-white/90">{risk.student_name}</h4>
                        <div className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-widest
                            ${risk.risk_level === 'critical' ? 'bg-red-500 text-white' : 'bg-white/10 text-white/40'}
                        `}>
                            {risk.risk_level}
                        </div>
                    </div>
                    
                    <div className="text-3xl font-bold tracking-tighter mb-4">{Math.round(risk.risk_score)}<em>% risk</em></div>
                    
                    <div className="flex flex-wrap gap-2 mb-4">
                        {risk.flags?.map(f => (
                            <span key={f} className="text-[9px] px-2 py-1 bg-red-500/10 text-red-300 font-bold uppercase rounded-md tracking-widest border border-red-500/20">
                                {f.replace('_', ' ')}
                            </span>
                        ))}
                    </div>

                    <button className="w-full bg-white/5 hover:bg-indigo-500 text-white/40 hover:text-white py-2.5 rounded-xl text-[10px] font-bold uppercase tracking-widest mt-2 transition-all">
                        Intervene (AI Coach)
                    </button>
                </div>
            )) : (
                <div className="col-span-full py-12 text-center text-white/20">
                    <Users size={48} className="mx-auto mb-4 opacity-10" />
                    <p className="font-medium">No behavioral risk detected in the current cohort.</p>
                </div>
            )}
        </div>
      </div>
    </div>
  )
}
