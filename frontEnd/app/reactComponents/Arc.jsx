export default function RouteArc({ origin, dest }) {
    const airports = {
        SFO: { x: 60,  y: 80, label: "SFO" },
        JFK: { x: 500, y: 80, label: "JFK" },
        ORD: { x: 260, y: 70, label: "ORD" },
        LAX: { x: 80,  y: 95, label: "LAX" },
        BOS: { x: 510, y: 65, label: "BOS" },
        ATL: { x: 350, y: 95, label: "ATL" },
    }

    const from = airports[origin] || airports.SFO
    const to   = airports[dest]   || airports.JFK

    // Control point sits above midpoint for the arc curve
    const cpX = (from.x + to.x) / 2
    const cpY = Math.min(from.y, to.y) - 60

    const d = `M ${from.x} ${from.y} Q ${cpX} ${cpY} ${to.x} ${to.y}`

    // Midpoint along quadratic for plane position
    const t = 0.5
    const planeX = (1-t)*(1-t)*from.x + 2*(1-t)*t*cpX + t*t*to.x
    const planeY = (1-t)*(1-t)*from.y + 2*(1-t)*t*cpY + t*t*to.y

    return (
        <svg viewBox="0 0 560 130" className="w-full" xmlns="http://www.w3.org/2000/svg">
        {/* Arc */}
        <path d={d} stroke="#c8902a" strokeWidth="1.5"
                strokeDasharray="5,4" fill="none" opacity="0.8"/>
        {/* Origin dot */}
        <circle cx={from.x} cy={from.y} r="4" fill="#1a1a1a"/>
        <text x={from.x} y={from.y + 16} fontSize="10"
                fill="#888" textAnchor="middle">{from.label}</text>
        {/* Dest dot */}
        <circle cx={to.x} cy={to.y} r="4" fill="#1a1a1a"/>
        <text x={to.x} y={to.y + 16} fontSize="10"
                fill="#888" textAnchor="middle">{to.label}</text>
        {/* Plane */}
        <text x={planeX} y={planeY - 8} fontSize="14"
                fill="#1a1a1a" textAnchor="middle">✈</text>
        </svg>
    )
}