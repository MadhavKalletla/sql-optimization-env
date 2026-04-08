'use client'

import { useEffect, useState } from 'react'

export function RobotWidget() {
  const [blink, setBlink] = useState(false)
  const [wave, setWave] = useState(false)

  useEffect(() => {
    // blink every 3s
    const blinkTimer = setInterval(() => {
      setBlink(true)
      setTimeout(() => setBlink(false), 150)
    }, 3000)

    // wave every 6s
    const waveTimer = setInterval(() => {
      setWave(true)
      setTimeout(() => setWave(false), 800)
    }, 6000)

    return () => {
      clearInterval(blinkTimer)
      clearInterval(waveTimer)
    }
  }, [])

  return (
    <div
      title="SQL Optimization AI Agent"
      style={{
        position: 'fixed',
        left: 16,
        bottom: 16,
        width: 120,
        height: 160,
        zIndex: 50,
        userSelect: 'none',
        filter: 'drop-shadow(0 0 16px #4A90D960)',
      }}
    >
      <style>{`
        @keyframes robot-float {
          0%, 100% { transform: translateY(0px); }
          50%       { transform: translateY(-6px); }
        }
        @keyframes robot-glow {
          0%, 100% { box-shadow: 0 0 8px #4A90D9, 0 0 20px #4A90D940; }
          50%       { box-shadow: 0 0 16px #00D4FF, 0 0 40px #00D4FF40; }
        }
        @keyframes antenna-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.4; transform: scale(1.4); }
        }
        @keyframes arm-wave {
          0%, 100% { transform: rotate(0deg); }
          25%       { transform: rotate(-40deg); }
          75%       { transform: rotate(10deg); }
        }
        @keyframes chest-scan {
          0%, 100% { opacity: 0.3; }
          50%       { opacity: 1; }
        }
        .robot-body  { animation: robot-float 3s ease-in-out infinite; }
        .robot-glow  { animation: robot-glow 2s ease-in-out infinite; }
        .ant-pulse   { animation: antenna-pulse 1.5s ease-in-out infinite; }
        .arm-wave    { animation: arm-wave 0.8s ease-in-out; }
        .chest-scan  { animation: chest-scan 2s ease-in-out infinite; }
      `}</style>

      <div className="robot-body" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0 }}>

        {/* Antenna */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 2 }}>
          <div
            className="ant-pulse"
            style={{ width: 8, height: 8, borderRadius: '50%', background: '#00D4FF', marginBottom: 2 }}
          />
          <div style={{ width: 2, height: 12, background: '#4A90D9', borderRadius: 1 }} />
        </div>

        {/* Head */}
        <div
          className="robot-glow"
          style={{
            width: 56,
            height: 44,
            borderRadius: 10,
            background: 'linear-gradient(160deg, #1a2550 0%, #0f1229 100%)',
            border: '2px solid #4A90D9',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            position: 'relative',
          }}
        >
          {/* Eyes */}
          <div style={{ display: 'flex', gap: 10 }}>
            {[0, 1].map(i => (
              <div
                key={i}
                style={{
                  width: 10,
                  height: blink ? 2 : 10,
                  borderRadius: blink ? 1 : '50%',
                  background: blink ? '#4A90D9' : 'linear-gradient(135deg, #00D4FF, #4A90D9)',
                  boxShadow: blink ? 'none' : '0 0 8px #00D4FF',
                  transition: 'height 0.08s, border-radius 0.08s',
                }}
              />
            ))}
          </div>
          {/* Mouth */}
          <div style={{ display: 'flex', gap: 2 }}>
            {[0,1,2,3].map(i => (
              <div key={i} style={{ width: 4, height: 2, background: '#4A90D980', borderRadius: 1 }} />
            ))}
          </div>
        </div>

        {/* Neck */}
        <div style={{ width: 20, height: 6, background: '#4A90D9', borderRadius: 2 }} />

        {/* Body */}
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          {/* Left arm */}
          <div
            className={wave ? 'arm-wave' : ''}
            style={{
              width: 10,
              height: 30,
              background: 'linear-gradient(180deg, #1a2550, #0f1229)',
              border: '1px solid #4A90D9',
              borderRadius: 5,
              marginRight: 2,
              transformOrigin: 'top center',
            }}
          />

          {/* Torso */}
          <div
            style={{
              width: 56,
              height: 54,
              borderRadius: 8,
              background: 'linear-gradient(160deg, #1a2550 0%, #0f1229 100%)',
              border: '2px solid #4A90D9',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 4,
              padding: 6,
            }}
          >
            {/* Chest panel */}
            <div
              className="chest-scan"
              style={{
                width: '80%',
                height: 4,
                background: 'linear-gradient(90deg, transparent, #00D4FF, transparent)',
                borderRadius: 2,
              }}
            />
            <div style={{ display: 'flex', gap: 4 }}>
              {[0,1,2].map(i => (
                <div
                  key={i}
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: 2,
                    background: i === 1 ? '#00D4FF' : '#4A90D9',
                    opacity: i === 1 ? 1 : 0.5,
                    boxShadow: i === 1 ? '0 0 6px #00D4FF' : 'none',
                  }}
                />
              ))}
            </div>
            <div style={{ fontSize: 7, color: '#4A90D9', fontFamily: 'monospace', fontWeight: 700, letterSpacing: 1 }}>
              SQL·RL
            </div>
          </div>

          {/* Right arm */}
          <div
            style={{
              width: 10,
              height: 30,
              background: 'linear-gradient(180deg, #1a2550, #0f1229)',
              border: '1px solid #4A90D9',
              borderRadius: 5,
              marginLeft: 2,
            }}
          />
        </div>

        {/* Legs */}
        <div style={{ display: 'flex', gap: 8, marginTop: 2 }}>
          {[0, 1].map(i => (
            <div
              key={i}
              style={{
                width: 14,
                height: 20,
                background: 'linear-gradient(180deg, #1a2550, #0f1229)',
                border: '1px solid #4A90D9',
                borderRadius: '0 0 6px 6px',
              }}
            />
          ))}
        </div>

        {/* Feet */}
        <div style={{ display: 'flex', gap: 4, marginTop: 1 }}>
          {[0, 1].map(i => (
            <div
              key={i}
              style={{
                width: 18,
                height: 7,
                background: '#4A90D9',
                borderRadius: '0 0 6px 6px',
              }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
