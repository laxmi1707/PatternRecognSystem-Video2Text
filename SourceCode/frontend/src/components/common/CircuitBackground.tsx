import { useEffect, useRef } from 'react';

type Icon = 'film' | 'play' | 'frame' | 'reel';

interface FloatingIcon {
  x: number;
  y: number;
  size: number;
  rotation: number;
  rotSpeed: number;
  vx: number;
  vy: number;
  opacity: number;
  icon: Icon;
}

function drawFilmStrip(ctx: CanvasRenderingContext2D, x: number, y: number, size: number) {
  const w = size;
  const h = size * 1.4;
  ctx.strokeRect(x - w / 2, y - h / 2, w, h);
  const holeSize = size * 0.1;
  const gap = h / 5;
  for (let i = 0; i < 4; i++) {
    const hy = y - h / 2 + gap * (i + 0.7);
    ctx.fillRect(x - w / 2 + 2, hy, holeSize, holeSize);
    ctx.fillRect(x + w / 2 - 2 - holeSize, hy, holeSize, holeSize);
  }
  ctx.strokeRect(x - w * 0.3, y - h * 0.25, w * 0.6, h * 0.45);
}

function drawPlayButton(ctx: CanvasRenderingContext2D, x: number, y: number, size: number) {
  ctx.beginPath();
  ctx.arc(x, y, size * 0.5, 0, Math.PI * 2);
  ctx.stroke();
  const s = size * 0.22;
  ctx.beginPath();
  ctx.moveTo(x - s * 0.4, y - s);
  ctx.lineTo(x - s * 0.4, y + s);
  ctx.lineTo(x + s * 0.8, y);
  ctx.closePath();
  ctx.fill();
}

function drawVideoFrame(ctx: CanvasRenderingContext2D, x: number, y: number, size: number) {
  const w = size * 1.2;
  const h = size * 0.75;
  const r = size * 0.06;
  ctx.beginPath();
  ctx.roundRect(x - w / 2, y - h / 2, w, h, r);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(x - w * 0.35, y - h / 2);
  ctx.lineTo(x - w * 0.35, y + h / 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(x + w * 0.35, y - h / 2);
  ctx.lineTo(x + w * 0.35, y + h / 2);
  ctx.stroke();
}

function drawReel(ctx: CanvasRenderingContext2D, x: number, y: number, size: number) {
  const r = size * 0.5;
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(x, y, r * 0.2, 0, Math.PI * 2);
  ctx.stroke();
  for (let i = 0; i < 3; i++) {
    const angle = (i * Math.PI * 2) / 3;
    ctx.beginPath();
    ctx.arc(x + Math.cos(angle) * r * 0.55, y + Math.sin(angle) * r * 0.55, r * 0.18, 0, Math.PI * 2);
    ctx.stroke();
  }
}

export function CircuitBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    const nodes: { x: number; y: number; r: number; vx: number; vy: number }[] = [];
    const icons: FloatingIcon[] = [];
    const iconTypes: Icon[] = ['film', 'play', 'frame', 'reel'];

    function resize() {
      canvas!.width = canvas!.offsetWidth;
      canvas!.height = canvas!.offsetHeight;
    }

    function init() {
      resize();
      const w = canvas!.width;
      const h = canvas!.height;

      nodes.length = 0;
      const count = Math.floor((w * h) / 14000);
      for (let i = 0; i < count; i++) {
        nodes.push({
          x: Math.random() * w,
          y: Math.random() * h,
          r: Math.random() * 2 + 1,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
        });
      }

      icons.length = 0;
      const iconCount = Math.floor((w * h) / 80000);
      for (let i = 0; i < iconCount; i++) {
        icons.push({
          x: Math.random() * w,
          y: Math.random() * h,
          size: 28 + Math.random() * 32,
          rotation: Math.random() * Math.PI * 2,
          rotSpeed: (Math.random() - 0.5) * 0.003,
          vx: (Math.random() - 0.5) * 0.15,
          vy: (Math.random() - 0.5) * 0.15,
          opacity: 0.06 + Math.random() * 0.08,
          icon: iconTypes[i % iconTypes.length],
        });
      }
    }

    function draw() {
      const w = canvas!.width;
      const h = canvas!.height;
      ctx!.clearRect(0, 0, w, h);

      // circuit nodes + edges
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        a.x += a.vx;
        a.y += a.vy;
        if (a.x < 0 || a.x > w) a.vx *= -1;
        if (a.y < 0 || a.y > h) a.vy *= -1;

        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dist = Math.hypot(a.x - b.x, a.y - b.y);
          if (dist < 150) {
            ctx!.beginPath();
            ctx!.moveTo(a.x, a.y);
            ctx!.lineTo(b.x, b.y);
            ctx!.strokeStyle = `rgba(99,102,241,${0.25 * (1 - dist / 150)})`;
            ctx!.lineWidth = 0.8;
            ctx!.stroke();
          }
        }

        ctx!.beginPath();
        ctx!.arc(a.x, a.y, a.r, 0, Math.PI * 2);
        ctx!.fillStyle = 'rgba(129,140,248,0.6)';
        ctx!.fill();
      }

      // floating film/video icons
      for (const ic of icons) {
        ic.x += ic.vx;
        ic.y += ic.vy;
        ic.rotation += ic.rotSpeed;
        if (ic.x < -60 || ic.x > w + 60) ic.vx *= -1;
        if (ic.y < -60 || ic.y > h + 60) ic.vy *= -1;

        ctx!.save();
        ctx!.translate(ic.x, ic.y);
        ctx!.rotate(ic.rotation);
        ctx!.strokeStyle = `rgba(129,140,248,${ic.opacity})`;
        ctx!.fillStyle = `rgba(129,140,248,${ic.opacity})`;
        ctx!.lineWidth = 1.2;

        switch (ic.icon) {
          case 'film': drawFilmStrip(ctx!, 0, 0, ic.size); break;
          case 'play': drawPlayButton(ctx!, 0, 0, ic.size); break;
          case 'frame': drawVideoFrame(ctx!, 0, 0, ic.size); break;
          case 'reel': drawReel(ctx!, 0, 0, ic.size); break;
        }

        ctx!.restore();
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
