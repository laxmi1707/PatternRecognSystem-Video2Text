import { useEffect, useRef } from 'react';

interface Neuron {
  x: number;
  y: number;
  r: number;
  vx: number;
  vy: number;
  pulse: number;       // 0..1 glow phase
  pulseSpeed: number;
  layer: number;       // visual depth (0=back, 1=mid, 2=front)
}

interface Signal {
  fromIdx: number;
  toIdx: number;
  t: number;    // 0..1 progress along the edge
  speed: number;
  opacity: number;
}

const ORANGE      = '239,124,0';
const ORANGE_LITE = '255,160,60';
const NAVY_GLOW   = '0,35,70';

export function CircuitBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    const neurons: Neuron[] = [];
    const signals: Signal[] = [];

    function resize() {
      canvas!.width  = canvas!.offsetWidth;
      canvas!.height = canvas!.offsetHeight;
    }

    function init() {
      resize();
      const w = canvas!.width;
      const h = canvas!.height;

      neurons.length = 0;
      signals.length = 0;

      // Spread neurons across the canvas in loose layers
      const count = Math.max(12, Math.floor((w * h) / 38000));
      for (let i = 0; i < count; i++) {
        const layer = i % 3;
        neurons.push({
          x: Math.random() * w,
          y: Math.random() * h,
          r: layer === 2 ? 3.5 : layer === 1 ? 2.5 : 1.8,
          vx: (Math.random() - 0.5) * (layer === 2 ? 0.18 : 0.28),
          vy: (Math.random() - 0.5) * (layer === 2 ? 0.18 : 0.28),
          pulse: Math.random(),
          pulseSpeed: 0.004 + Math.random() * 0.008,
          layer,
        });
      }
    }

    // Seed a few signals each frame
    function maybeSpawnSignal() {
      if (signals.length > 40) return;
      if (Math.random() > 0.04) return;
      const fromIdx = Math.floor(Math.random() * neurons.length);
      const a = neurons[fromIdx];
      let bestIdx = -1;
      let bestDist = Infinity;
      for (let j = 0; j < neurons.length; j++) {
        if (j === fromIdx) continue;
        const d = Math.hypot(neurons[j].x - a.x, neurons[j].y - a.y);
        if (d < 160 && d < bestDist) { bestDist = d; bestIdx = j; }
      }
      if (bestIdx !== -1) {
        signals.push({
          fromIdx,
          toIdx: bestIdx,
          t: 0,
          speed: 0.006 + Math.random() * 0.009,
          opacity: 0.2 + Math.random() * 0.2,
        });
      }
    }

    function draw() {
      const w = canvas!.width;
      const h = canvas!.height;
      ctx!.clearRect(0, 0, w, h);

      // — update neurons —
      for (const n of neurons) {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;
        n.pulse = (n.pulse + n.pulseSpeed) % 1;
      }

      // — draw synaptic edges —
      for (let i = 0; i < neurons.length; i++) {
        const a = neurons[i];
        for (let j = i + 1; j < neurons.length; j++) {
          const b = neurons[j];
          const dist = Math.hypot(a.x - b.x, a.y - b.y);
          const maxDist = 155;
          if (dist > maxDist) continue;
          const alpha = 0.04 * (1 - dist / maxDist);
          ctx!.beginPath();
          ctx!.moveTo(a.x, a.y);
          ctx!.lineTo(b.x, b.y);
          ctx!.strokeStyle = `rgba(${ORANGE},${alpha})`;
          ctx!.lineWidth = 0.5;
          ctx!.stroke();
        }
      }

      // — draw signal pulses travelling along edges —
      maybeSpawnSignal();
      for (let s = signals.length - 1; s >= 0; s--) {
        const sig = signals[s];
        sig.t += sig.speed;
        if (sig.t >= 1) { signals.splice(s, 1); continue; }

        const a = neurons[sig.fromIdx];
        const b = neurons[sig.toIdx];
        const px = a.x + (b.x - a.x) * sig.t;
        const py = a.y + (b.y - a.y) * sig.t;

        // Glow halo
        const grd = ctx!.createRadialGradient(px, py, 0, px, py, 7);
        grd.addColorStop(0, `rgba(${ORANGE_LITE},${sig.opacity * 0.9})`);
        grd.addColorStop(0.5, `rgba(${ORANGE},${sig.opacity * 0.4})`);
        grd.addColorStop(1, `rgba(${ORANGE},0)`);
        ctx!.beginPath();
        ctx!.arc(px, py, 7, 0, Math.PI * 2);
        ctx!.fillStyle = grd;
        ctx!.fill();

        // Core dot
        ctx!.beginPath();
        ctx!.arc(px, py, 2.2, 0, Math.PI * 2);
        ctx!.fillStyle = `rgba(${ORANGE_LITE},${sig.opacity})`;
        ctx!.fill();
      }

      // — draw neuron bodies —
      for (const n of neurons) {
        const glowAlpha = 0.02 + Math.sin(n.pulse * Math.PI * 2) * 0.02;
        const coreAlpha = 0.12 + Math.sin(n.pulse * Math.PI * 2) * 0.05;

        // Soft glow
        const grd = ctx!.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 4);
        grd.addColorStop(0, `rgba(${ORANGE},${glowAlpha})`);
        grd.addColorStop(0.5, `rgba(${NAVY_GLOW},${glowAlpha * 0.3})`);
        grd.addColorStop(1, `rgba(${NAVY_GLOW},0)`);
        ctx!.beginPath();
        ctx!.arc(n.x, n.y, n.r * 4, 0, Math.PI * 2);
        ctx!.fillStyle = grd;
        ctx!.fill();

        // Core
        ctx!.beginPath();
        ctx!.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx!.fillStyle = `rgba(${ORANGE},${coreAlpha})`;
        ctx!.fill();

        // Dendrite spikes on front-layer neurons
        if (n.layer === 2) {
          ctx!.strokeStyle = `rgba(${ORANGE},${glowAlpha * 1.5})`;
          ctx!.lineWidth = 0.6;
          for (let k = 0; k < 6; k++) {
            const angle = (k / 6) * Math.PI * 2 + n.pulse * Math.PI;
            const len = n.r * (2.5 + Math.sin(n.pulse * Math.PI * 2 + k) * 1.2);
            ctx!.beginPath();
            ctx!.moveTo(n.x + Math.cos(angle) * n.r, n.y + Math.sin(angle) * n.r);
            ctx!.lineTo(n.x + Math.cos(angle) * len, n.y + Math.sin(angle) * len);
            ctx!.stroke();
          }
        }
      }

      animId = requestAnimationFrame(draw);
    }

    init();
    draw();
    window.addEventListener('resize', init);
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', init);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  );
}
