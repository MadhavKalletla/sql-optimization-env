export function QueryViz() {
  return (
    <div className="w-full h-full min-h-[320px] flex flex-col justify-center gap-8 relative items-center text-xs font-mono select-none">
      <style>{`
        @keyframes pulse-red {
          0% { box-shadow: 0 0 0px #FF5252; text-shadow: 0 0 0px #FF5252; }
          50% { box-shadow: 0 0 20px #FF5252; text-shadow: 0 0 10px #FF5252; }
          100% { box-shadow: 0 0 0px #FF5252; text-shadow: 0 0 0px #FF5252; }
        }
        @keyframes flow-line {
          0% { width: 0%; opacity: 1; }
          60% { width: 100%; opacity: 1; }
          100% { width: 100%; opacity: 0; }
        }
        @keyframes fade-in-up {
          0% { opacity: 0; transform: translateY(10px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes shrink-bar {
          0%, 20% { width: 100%; }
          40%, 80% { width: var(--target-width); }
          100% { width: 100%; }
        }
      `}</style>
      
      <div className="flex w-full max-w-lg justify-between items-center px-4">
        {/* LEFT */}
        <div className="flex flex-col items-center gap-2">
          <div
            className="w-24 h-24 rounded-2xl flex items-center justify-center border-2 border-[#FF5252] bg-[#FF525215]"
            style={{ animation: 'pulse-red 2s infinite' }}
          >
            <div className="text-center">
              <div className="text-[#FF5252] font-bold text-[10px]">SCAN</div>
              <div className="text-slate-400 mt-1">50.0k</div>
            </div>
          </div>
          <span className="font-bold tracking-widest text-[#FF5252]">SLOW QUERY</span>
        </div>

        {/* CENTER */}
        <div className="flex flex-col flex-1 items-center justify-center relative px-6">
          <div 
            className="text-center font-bold text-[#00E676] mb-2"
            style={{ animation: 'fade-in-up 1s ease-out forwards' }}
          >
            12.4x faster
          </div>
          <div className="w-full h-0.5 bg-slate-800 relative rounded-full overflow-hidden">
             <div 
               className="absolute top-0 left-0 h-full bg-gradient-to-r from-[#FF5252] to-[#00E676]" 
               style={{ animation: 'flow-line 2s infinite' }}
             />
          </div>
          {/* Arrow head static at right */}
          <div className="absolute right-5 top-1/2 -translate-y-1/2 translate-y-3 translate-x-1/2 w-2 h-2 rotate-45 border-t-2 border-r-2 border-[#00E676]"></div>
        </div>

        {/* RIGHT */}
        <div className="flex flex-col items-center gap-2">
          <div className="w-24 h-24 rounded-2xl flex items-center justify-center border-2 border-[#00E676] bg-[#00E67615]">
            <div className="text-center">
              <div className="text-[#00E676] font-bold text-[10px]">INDEX</div>
              <div className="text-slate-400 mt-1">142</div>
            </div>
          </div>
          <span className="font-bold tracking-widest text-[#00E676]">OPTIMIZED</span>
        </div>
      </div>

      {/* BOTTOM METRICS */}
      <div className="flex w-full max-w-lg gap-6 px-4 mt-4">
        {[
          { label: 'ROWS', to: '5%', color: '#FFD740' },
          { label: 'COST', to: '15%', color: '#4A90D9' },
          { label: 'TIME', to: '10%', color: '#E040FB' },
        ].map((metric) => (
          <div key={metric.label} className="flex-1 flex flex-col gap-1">
            <span className="text-[10px] text-slate-500">{metric.label}</span>
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden relative">
              <div
                className="absolute top-0 left-0 h-full rounded-full"
                style={{ 
                  backgroundColor: metric.color,
                  '--target-width': metric.to,
                  animation: 'shrink-bar 4s infinite' 
                } as React.CSSProperties}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
