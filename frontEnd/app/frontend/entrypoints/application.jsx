import { createRoot } from "react-dom/client";
import DelayGauge from "../../reactComponents/Gauge";
import RouteArc from "../../reactComponents/Arc";

// Mount the DelayGauge component whenever id="delay-gauge" exists
const gaugeElement = document.getElementById("delay-gauge")

if (gaugeElement) {
    const prob = parseFloat(gaugeElement.dataset.prob)
    createRoot(gaugeElement).render(<DelayGauge prob={prob} />)
}

// Mount the RouteArc component whenever id="route-arc" exists
const arcElement = document.getElementById("route-arc")
if (arcElement) {
    const origin = arcElement.dataset.origin
    const dest = arcElement.dataset.dest

    createRoot(arcElement).render(<RouteArc origin={origin} dest={dest} />)
}


document.addEventListener("DOMContentLoaded", setupSwap)
document.addEventListener("turbo:load", setupSwap)

function setupSwap() {
  const swapBtn = document.getElementById("swap-airports")
  if (!swapBtn) return

  swapBtn.addEventListener("click", () => {
    const originSelect = document.querySelector("select[name='origin']")
    const destSelect   = document.querySelector("select[name='dest']")
    if (!originSelect || !destSelect) return

    const temp         = originSelect.value
    originSelect.value = destSelect.value
    destSelect.value   = temp
  })
}
