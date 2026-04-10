'use client'

import { motion, Variants } from 'framer-motion'
import { DollarSign, Cpu, Clock, Database } from 'lucide-react'
import { AgentPlan } from './agent-plan'

const STATS = [
  {
    icon: DollarSign,
    color: '#ff6b6b',
    heading: '$4.7M',
    subheading: 'Average cost per data breach',
    body: 'Unoptimized queries expose companies like Uber and Twitter to prolonged vulnerability windows'
  },
  {
    icon: Cpu,
    color: '#ffd93d',
    heading: '8× RAM Spike',
    subheading: 'Cartesian joins on large tables',
    body: 'Facebook and Netflix engineers cite runaway memory from missing JOIN conditions as a top-3 incident cause'
  },
  {
    icon: Clock,
    color: '#6bcb77',
    heading: '60s → 1s',
    subheading: 'N+1 query fix impact',
    body: 'Shopify reduced checkout latency 60× by replacing correlated subqueries with a single JOIN'
  },
  {
    icon: Database,
    color: '#4d96ff',
    heading: '1 Billion+ Rows',
    subheading: 'Where full scans kill systems',
    body: 'Google and Amazon run query review pipelines because one missing index on a billion-row table can take down a service'
  }
]

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
}

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } }
}

export function WhyOptimizationMatters() {
  return (
    <section 
      style={{ 
        minHeight: '100vh', 
        backgroundColor: '#0a0f1e',
      }}
      className="w-full flex flex-col justify-center items-center py-[80px] px-8 md:px-[120px]"
    >
      <motion.div 
        className="w-full max-w-6xl mx-auto flex flex-col items-center text-center"
        style={{ marginBottom: 48 }}
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.6 }}
      >
        <h2 style={{ fontSize: '2rem', fontWeight: 700, color: 'white', marginBottom: '0.5rem' }}>
          Why SQL Optimization Matters
        </h2>
        <p style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.55)', maxWidth: '600px' }}>
          The real cost of unoptimized queries at scale — problems this environment trains AI to solve
        </p>
      </motion.div>

      <div className="w-full max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-12">
        
        {/* LEFT SIDE: Robot (40%) */}
        <motion.div 
          className="w-full md:w-[40%] flex justify-center items-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <AgentPlan />
        </motion.div>

        {/* RIGHT SIDE: Stat Boxes (60%) */}
        <motion.div 
          className="w-full md:w-[60%] grid grid-cols-1 sm:grid-cols-2 gap-6"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
        >
          {STATS.map((stat, i) => {
            const Icon = stat.icon
            return (
              <motion.div
                key={i}
                variants={itemVariants}
                className="relative overflow-hidden group cursor-default"
                style={{
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 16,
                  padding: 24,
                  minHeight: 160,
                  transition: 'all 0.3s ease'
                }}
              >
                 {/* Top accent line */}
                 <div className="absolute top-0 left-0 right-0 h-1" style={{ backgroundColor: stat.color }} />
                 
                 {/* Subtle Hover Glow */}
                 <div 
                   className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" 
                   style={{ background: `radial-gradient(circle at center, ${stat.color}15 0%, transparent 70%)` }} 
                 />

                 <div className="flex items-start gap-4 relative z-10 w-full">
                   <div className="p-2 rounded-lg shrink-0" style={{ background: `${stat.color}20` }}>
                     <Icon size={24} color={stat.color} />
                   </div>
                   <div className="flex flex-col">
                     <h3 style={{ color: stat.color, fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1.2 }}>
                       {stat.heading}
                     </h3>
                     <p style={{ color: 'white', fontSize: '0.85rem', fontWeight: 600, marginTop: '2px', marginBottom: '8px', lineHeight: 1.3 }}>
                       {stat.subheading}
                     </p>
                     <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem', lineHeight: 1.5, paddingRight: '4px' }}>
                       {stat.body}
                     </p>
                   </div>
                 </div>
              </motion.div>
            )
          })}
        </motion.div>

      </div>
    </section>
  )
}
