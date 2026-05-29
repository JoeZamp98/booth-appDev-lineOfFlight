import { useEffect, useRef, useState, useId } from 'react';

export default function DelayGauge({ prob }) {
    const pathRef = useRef(null)
    const [revealed, setRevealed] = useState(false)
    const uid = useId().replace(/:/g, "")

    const toRad = (deg) => (deg * Math.PI) / 180
    const cx = 70, cy = 70, r = 52

    // Gauge sweeps the upper dome, bottom-left → bottom-right
    const startAngle = 215
    const endAngle   = 325
    const clamped    = Math.max(0, Math.min(1, Number(prob) || 0))
    const fillAngle  = startAngle + clamped * (endAngle - startAngle)

    const polarPoint = (angle) => ({
      x: +(cx + r * Math.cos(toRad(angle))).toFixed(2),
      y: +(cy + r * Math.sin(toRad(angle))).toFixed(2),
    })

    const start    = polarPoint(startAngle)
    const end      = polarPoint(endAngle)
    const fillEnd  = polarPoint(fillAngle)
    const largeArc  = endAngle - startAngle > 180 ? 1 : 0
    const fillLarge = fillAngle - startAngle > 180 ? 1 : 0

    const trackPath = `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`
    const fillPath  = clamped > 0
      ? `M ${start.x} ${start.y} A ${r} ${r} 0 ${fillLarge} 1 ${fillEnd.x} ${fillEnd.y}`
      : null

    const color      = clamped > 0.5 ? "#c0392b" : clamped > 0.25 ? "#c8902a" : "#4a8c5c"
    const colorLight = clamped > 0.5 ? "#e07065" : clamped > 0.25 ? "#e0b259" : "#7bb78c"

    useEffect(() => {
      const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches

      if (pathRef.current && fillPath) {
        const length = pathRef.current.getTotalLength()
        if (reduceMotion) {
          pathRef.current.style.strokeDashoffset = 0
        } else {
          pathRef.current.style.strokeDasharray  = length
          pathRef.current.style.strokeDashoffset = length
          requestAnimationFrame(() => {
            if (!pathRef.current) return
            pathRef.current.style.transition = "stroke-dashoffset 1.1s cubic-bezier(0.22, 1, 0.36, 1)"
            pathRef.current.style.strokeDashoffset = 0
          })
        }
      }

      const t = setTimeout(() => setRevealed(true), reduceMotion ? 0 : 700)
      return () => clearTimeout(t)
    }, [prob])

    return (
      <svg viewBox="0 0 140 100" xmlns="http://www.w3.org/2000/svg"
           className="w-full" style={{ overflow: "visible" }}>
        <defs>
          <linearGradient id={`gaugeGrad-${uid}`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%"   stopColor={colorLight} />
            <stop offset="100%" stopColor={color} />
          </linearGradient>
          <filter id={`gaugeGlow-${uid}`} x="-40%" y="-40%" width="180%" height="180%">
            <feDropShadow dx="0" dy="1.5" stdDeviation="2"
                          floodColor={color} floodOpacity="0.28" />
          </filter>
        </defs>

        {/* Track */}
        <path d={trackPath} stroke="#ECE8E1" strokeWidth="9"
              fill="none" strokeLinecap="round" />

        {/* Animated fill */}
        {fillPath && (
          <path ref={pathRef} d={fillPath}
                stroke={`url(#gaugeGrad-${uid})`} strokeWidth="9"
                fill="none" strokeLinecap="round"
                filter={`url(#gaugeGlow-${uid})`} />
        )}

        {/* Knob at the tip of the fill */}
        {fillPath && (
          <circle cx={fillEnd.x} cy={fillEnd.y} r="4.5"
                  fill="#fff" stroke={color} strokeWidth="2.5"
                  style={{
                    opacity: revealed ? 1 : 0,
                    transition: "opacity 0.35s ease-out",
                  }} />
        )}

        {/* Center label */}
        <text x="70" y="66" textAnchor="middle" fontSize="21"
              fontWeight="500" fill={color}
              style={{
                opacity: revealed ? 1 : 0,
                transition: "opacity 0.45s ease-out",
              }}>
          {Math.round(clamped * 100)}%
        </text>
        <text x="70" y="79" textAnchor="middle" fontSize="6.5"
              letterSpacing="1.5" fill="#b4ada2">
          DELAY PROBABILITY
        </text>
      </svg>
    )
}
