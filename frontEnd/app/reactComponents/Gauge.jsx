import { useEffect, useRef } from 'react';

export default function DelayGauge({ prob }) {
    const pathRef = useRef(null)
  
    // Gauge goes from 215° to 325° (bottom-left to bottom-right arc)
    const toRad = (deg) => (deg * Math.PI) / 180
    const cx = 70, cy = 70, r = 52
  
    const startAngle = 215
    const endAngle   = 325
    const fillAngle  = startAngle + (prob * (endAngle - startAngle))
  
    const polarPoint = (angle) => ({
      x: (cx + r * Math.cos(toRad(angle))).toFixed(2),
      y: (cy + r * Math.sin(toRad(angle))).toFixed(2),
    })
  
    const start    = polarPoint(startAngle)
    const end      = polarPoint(endAngle)
    const fillEnd  = polarPoint(fillAngle)
    const largeArc = endAngle - startAngle > 180 ? 1 : 0
    const fillLarge = fillAngle - startAngle > 180 ? 1 : 0
  
    const trackPath = `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`
    const fillPath  = prob > 0
      ? `M ${start.x} ${start.y} A ${r} ${r} 0 ${fillLarge} 1 ${fillEnd.x} ${fillEnd.y}`
      : null
  
    const color = prob > 0.5 ? "#c0392b" : prob > 0.25 ? "#c8902a" : "#4a8c5c"
  
    useEffect(() => {
      if (!pathRef.current || !fillPath) return
      const length = pathRef.current.getTotalLength()
      pathRef.current.style.strokeDasharray  = length
      pathRef.current.style.strokeDashoffset = length
      // Trigger animation after mount
      requestAnimationFrame(() => {
        pathRef.current.style.transition = "stroke-dashoffset 1s ease-out"
        pathRef.current.style.strokeDashoffset = 0
      })
    }, [prob])
  
    return (
      <svg viewBox="0 0 140 100" xmlns="http://www.w3.org/2000/svg" className="w-full">
        {/* Track */}
        <path d={trackPath} stroke="#F0ECE8" strokeWidth="10"
              fill="none" strokeLinecap="round"/>
        {/* Animated fill */}
        {fillPath && (
          <path ref={pathRef} d={fillPath}
                stroke={color} strokeWidth="10"
                fill="none" strokeLinecap="round"/>
        )}
        {/* Label */}
        <text x="70" y="68" textAnchor="middle" fontSize="18"
              fontWeight="300" fill={color}>
          {Math.round(prob * 100)}%
        </text>
        <text x="70" y="80" textAnchor="middle" fontSize="7" fill="#aaa">
          DELAY PROBABILITY
        </text>
      </svg>
    )
}