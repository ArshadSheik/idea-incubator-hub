/**
 * msg-fx.js  –  Same hierarchical network as bg-fx.js, scoped to #msgCanvas.
 * 4 hub nodes form large structures; data packets travel hub↔hub / hub↔mid.
 */
(function () {
  'use strict';

  const canvas = document.getElementById('msgCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W, H, raf, tick = 0, nodes, packets;

  const C = {
    orange: { r: 255, g:  90, b:  31 },
    violet: { r:  91, g:  63, b: 255 },
    mint  : { r:   0, g: 217, b: 163 },
    blue  : { r:  59, g: 130, b: 246 },
    white : { r: 255, g: 255, b: 255 },
  };

  const CFG = {
    hubCount  :  4,
    midCount  : 16,
    leafCount : 40,
    hubHub    : 700,
    hubMid    : 260,
    midMid    : 160,
    midLeaf   : 110,
    maxPackets: 16,
    packetHz  : 20,
    hubSpd    : 0.09,
    midSpd    : 0.16,
    leafSpd   : 0.24,
  };

  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  function dist2(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y;
    return dx * dx + dy * dy;
  }

  function drawEdge(a, b, alpha, lw, r, g, b_) {
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = `rgba(${r},${g},${b_},${alpha})`;
    ctx.lineWidth   = lw;
    ctx.stroke();
  }

  /* ── Node ── */
  class Node {
    constructor(tier) {
      this.tier = tier;
      this.x  = 80 + Math.random() * (W - 160);
      this.y  = 80 + Math.random() * (H - 160);
      const ang = Math.random() * Math.PI * 2;
      const spd = tier === 1 ? CFG.hubSpd : tier === 2 ? CFG.midSpd : CFG.leafSpd;
      this.vx = Math.cos(ang) * spd * (0.5 + Math.random() * 0.8);
      this.vy = Math.sin(ang) * spd * (0.5 + Math.random() * 0.8);
      this.wo = Math.random() * Math.PI * 2;
      this.ws = 0.004 + Math.random() * 0.006;
      this.r  = tier === 1 ? 4.5 : tier === 2 ? 2.2 : 1.1;
      this.c  = tier === 1 ? C.orange
              : tier === 2 ? C.violet
              : (Math.random() < 0.5 ? C.mint : C.blue);
    }

    update() {
      this.wo += this.ws;
      this.vx += Math.cos(this.wo) * 0.003;
      this.vy += Math.sin(this.wo) * 0.003;
      const cap = this.tier === 1 ? 0.13 : this.tier === 2 ? 0.22 : 0.30;
      const s   = Math.hypot(this.vx, this.vy);
      if (s > cap) { this.vx *= 0.97; this.vy *= 0.97; }
      this.x += this.vx;
      this.y += this.vy;
      const m = 60;
      if (this.x < m)     this.vx += 0.025;
      if (this.x > W - m) this.vx -= 0.025;
      if (this.y < m)     this.vy += 0.025;
      if (this.y > H - m) this.vy -= 0.025;
    }

    draw(alpha) {
      const { r, g, b } = this.c;
      /* sharp core dot only — no glow, no flare */
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r},${g},${b},${Math.min(1, alpha)})`;
      ctx.fill();
    }
  }

  /* ── Packet ── */
  class Packet {
    constructor(a, b) {
      this.a     = a;
      this.b     = b;
      this.t     = 0;
      this.speed = 0.005 + Math.random() * 0.007;
      this.trail = [];
    }
    get done() { return this.t >= 1; }
    get pos()  {
      return {
        x: this.a.x + (this.b.x - this.a.x) * this.t,
        y: this.a.y + (this.b.y - this.a.y) * this.t,
      };
    }
    update() {
      const p = this.pos;
      this.trail.push({ x: p.x, y: p.y });
      if (this.trail.length > 16) this.trail.shift();
      this.t += this.speed;
    }
    draw(alpha) {
      const { r, g, b } = C.white;
      const p = this.pos;
      for (let i = 1; i < this.trail.length; i++) {
        const pct = i / this.trail.length;
        ctx.beginPath();
        ctx.moveTo(this.trail[i - 1].x, this.trail[i - 1].y);
        ctx.lineTo(this.trail[i].x,     this.trail[i].y);
        ctx.strokeStyle = `rgba(${r},${g},${b},${pct * pct * alpha * 0.75})`;
        ctx.lineWidth   = pct * 1.8;
        ctx.lineCap     = 'round';
        ctx.stroke();
      }
      const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, 10);
      grd.addColorStop(0, `rgba(${r},${g},${b},${alpha * 0.7})`);
      grd.addColorStop(1, `rgba(${r},${g},${b},0)`);
      ctx.beginPath();
      ctx.arc(p.x, p.y, 10, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
      ctx.fill();
    }
  }

  /* ── Resize / Init ── */
  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    W = canvas.width  = Math.round(rect.width)  || 900;
    H = canvas.height = Math.round(rect.height) || 600;
  }

  function init() {
    const hubs  = Array.from({ length: CFG.hubCount  }, () => new Node(1));
    const mids  = Array.from({ length: CFG.midCount  }, () => new Node(2));
    const leafs = Array.from({ length: CFG.leafCount }, () => new Node(3));
    nodes   = [...hubs, ...mids, ...leafs];
    packets = [];
    tick    = 0;
  }

  /* ── Render loop ── */
  function frame() {
    tick++;
    ctx.clearRect(0, 0, W, H);

    const dark    = isDark();
    const nodeA   = dark ? 0.95 : 0.26;
    const packetA = dark ? 0.95 : 0.45;

    const hubs  = nodes.filter(n => n.tier === 1);
    const mids  = nodes.filter(n => n.tier === 2);
    const leafs = nodes.filter(n => n.tier === 3);

    const hhR2  = CFG.hubHub  * CFG.hubHub;
    const hmR2  = CFG.hubMid  * CFG.hubMid;
    const mmR2  = CFG.midMid  * CFG.midMid;
    const mlR2  = CFG.midLeaf * CFG.midLeaf;

    /* Hub ↔ Hub */
    for (let i = 0; i < hubs.length; i++) {
      for (let j = i + 1; j < hubs.length; j++) {
        if (dist2(hubs[i], hubs[j]) < hhR2) {
          const { r, g, b } = hubs[i].c;
          drawEdge(hubs[i], hubs[j], dark ? 0.30 : 0.10, 1.0, r, g, b);
        }
      }
    }

    /* Hub ↔ Mid (nearest 4) */
    for (const h of hubs) {
      const near = mids
        .map(m => ({ m, d2: dist2(h, m) }))
        .filter(x => x.d2 < hmR2)
        .sort((a, b) => a.d2 - b.d2)
        .slice(0, 4);
      for (const { m } of near) {
        const { r, g, b } = h.c;
        drawEdge(h, m, dark ? 0.18 : 0.07, 0.6, r, g, b);
      }
    }

    /* Mid ↔ Mid */
    for (let i = 0; i < mids.length; i++) {
      for (let j = i + 1; j < mids.length; j++) {
        if (dist2(mids[i], mids[j]) < mmR2) {
          const { r, g, b } = mids[i].c;
          drawEdge(mids[i], mids[j], dark ? 0.10 : 0.04, 0.4, r, g, b);
        }
      }
    }

    /* Mid ↔ Leaf (nearest 3) */
    for (const m of mids) {
      const near = leafs
        .map(l => ({ l, d2: dist2(m, l) }))
        .filter(x => x.d2 < mlR2)
        .sort((a, b) => a.d2 - b.d2)
        .slice(0, 3);
      for (const { l } of near) {
        const { r, g, b } = l.c;
        drawEdge(m, l, dark ? 0.07 : 0.025, 0.3, r, g, b);
      }
    }

    /* Nodes */
    for (const n of nodes) { n.update(); n.draw(nodeA); }

    /* Packets */
    if (tick % CFG.packetHz === 0 && packets.length < CFG.maxPackets) {
      const eligible = [];
      for (let i = 0; i < hubs.length; i++) {
        for (let j = i + 1; j < hubs.length; j++) {
          if (dist2(hubs[i], hubs[j]) < hhR2) eligible.push([hubs[i], hubs[j]]);
        }
        const near = mids.filter(m => dist2(hubs[i], m) < hmR2);
        if (near.length) eligible.push([hubs[i], near[Math.floor(Math.random() * near.length)]]);
      }
      if (eligible.length) {
        const [a, b] = eligible[Math.floor(Math.random() * eligible.length)];
        packets.push(new Packet(a, b));
      }
    }
    packets = packets.filter(p => !p.done);
    for (const p of packets) { p.update(); p.draw(packetA); }

    raf = requestAnimationFrame(frame);
  }

  /* ── Boot ── */
  resize(); init(); frame();

  new ResizeObserver(() => { cancelAnimationFrame(raf); resize(); init(); frame(); })
    .observe(canvas.parentElement);

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) cancelAnimationFrame(raf);
    else { resize(); init(); frame(); }
  });
})();
