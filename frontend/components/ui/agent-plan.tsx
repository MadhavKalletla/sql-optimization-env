'use client'

import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'

export function AgentPlan() {
  const [blink, setBlink] = useState(false)

  useEffect(() => {
    const blinkTimer = setInterval(() => {
      setBlink(true)
      setTimeout(() => setBlink(false), 150)
    }, 3000)
    return () => clearInterval(blinkTimer)
  }, [])

  return (
    <motion.div
      className="relative flex flex-col items-center justify-center cursor-pointer"
      style={{ width: 280, height: 320, perspective: 1000 }}
      whileHover={{ scale: 1.05, rotateY: 15, rotateX: -5 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
    >
      <style>{`
        @keyframes agent-float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-15px); }
        }
        @keyframes agent-glow {
          0%, 100% { box-shadow: 0 0 20px #4A90D9, 0 0 40px #4A90D940; border-color: #4A90D9; }
          50% { box-shadow: 0 0 40px #00D4FF, 0 0 80px #00D4FF40; border-color: #00D4FF; }
        }
        @keyframes pulse-ring {
          0% { transform: scale(0.6) rotateX(75deg); opacity: 0.8; }
          50% { transform: scale(1.0) rotateX(75deg); opacity: 0.2; }
          100% { transform: scale(0.6) rotateX(75deg); opacity: 0.8; }
        }
      `}</style>
      
      {/* Robot Base/Container with float animation */}
      <div 
        className="flex flex-col items-center justify-center relative"
        style={{ animation: 'agent-float 3s ease-in-out infinite', zIndex: 10 }}
      >
        {/* Antenna */}
        <div className="flex flex-col items-center mb-1">
          <div style={{ width: 14, height: 14, borderRadius: '50%', background: '#00D4FF', boxShadow: '0 0 10px #00D4FF' }} />
          <div style={{ width: 4, height: 24, background: '#4A90D9' }} />
        </div>

        {/* Head */}
        <div
          style={{
            width: 120, height: 90, borderRadius: 20,
            background: 'linear-gradient(160deg, #1a2550 0%, #0f1229 100%)',
            border: '3px solid', // Border color handled by animation
            animation: 'agent-glow 2s ease-in-out infinite',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12
          }}
        >
          {/* Eyes */}
          <div className="flex gap-6 mt-2">
            {[0, 1].map(i => (
              <div
                key={i}
                style={{
                  width: 20, height: blink ? 4 : 20,
                  borderRadius: blink ? 2 : '50%',
                  background: blink ? '#4A90D9' : 'linear-gradient(135deg, #00D4FF, #4A90D9)',
                  boxShadow: blink ? 'none' : '0 0 16px #00D4FF',
                  transition: 'height 0.1s, border-radius 0.1s'
                }}
              />
            ))}
          </div>
          {/* Mouth */}
          <div className="flex gap-2">
            {[0,1,2,3].map(i => (
              <div key={i} style={{ width: 8, height: 4, background: '#4A90D980', borderRadius: 2 }} />
            ))}
          </div>
        </div>

        {/* Neck */}
        <div style={{ width: 36, height: 12, background: '#4A90D9', borderRadius: 4, margin: '2px 0' }} />

        {/* Body Container */}
        <div className="flex items-center">
          {/* Left Arm */}
          <div style={{ width: 20, height: 70, background: 'linear-gradient(180deg, #1a2550, #0f1229)', border: '2px solid #4A90D9', borderRadius: 10, marginRight: 4, transform: 'rotate(15deg)', transformOrigin: 'top center' }} />
          
          {/* Torso */}
          <div
            style={{
              width: 120, height: 110, borderRadius: 16,
              background: 'linear-gradient(160deg, #1a2550 0%, #0f1229 100%)',
              border: '3px solid #4A90D9',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8, padding: 12,
              boxShadow: 'inset 0 0 20px rgba(74, 144, 217, 0.2)'
            }}
          >
             <div style={{ width: '80%', height: 6, background: 'linear-gradient(90deg, transparent, #00D4FF, transparent)', borderRadius: 3, opacity: 0.8 }} />
             <div className="flex gap-3 mt-1">
               {[0,1,2].map(i => (
                 <div key={i} style={{ width: 14, height: 14, borderRadius: 3, background: i === 1 ? '#00D4FF' : '#4A90D9', opacity: i === 1 ? 1 : 0.5, boxShadow: i === 1 ? '0 0 8px #00D4FF' : 'none' }} />
               ))}
             </div>
             <div style={{ fontSize: 16, color: '#4A90D9', fontFamily: 'monospace', fontWeight: 800, letterSpacing: 2, marginTop: 4 }}>
               SQL·RL
             </div>
          </div>

          {/* Right Arm */}
          <div style={{ width: 20, height: 70, background: 'linear-gradient(180deg, #1a2550, #0f1229)', border: '2px solid #4A90D9', borderRadius: 10, marginLeft: 4, transform: 'rotate(-15deg)', transformOrigin: 'top center' }} />
        </div>

        {/* Legs / Thruster Base */}
        <div className="flex gap-6 mt-1">
            {[0, 1].map(i => (
              <div key={i} style={{ width: 28, height: 32, background: 'linear-gradient(180deg, #172045, #0f1229)', border: '2px solid #4A90D9', borderTop: 'none', borderRadius: '0 0 12px 12px' }} />
            ))}
        </div>
        <div className="flex gap-2 justify-center w-full relative top-[-4px]">
           <div style={{ width: 60, height: 10, background: '#00D4FF', borderRadius: '50%', filter: 'blur(3px)', opacity: 0.9 }} />
        </div>
      </div>

      {/* Pulsing ring underneath */}
      <div 
        className="absolute"
        style={{
          width: 240, height: 240,
          borderRadius: '50%',
          border: '6px solid rgba(0, 212, 255, 0.5)',
          animation: 'pulse-ring 3s ease-in-out infinite',
          zIndex: 0,
          bottom: -90,
          boxShadow: '0 0 30px rgba(0, 212, 255, 0.4), inset 0 0 30px rgba(0, 212, 255, 0.4)'
        }}
      />
    </motion.div>
  )
}
