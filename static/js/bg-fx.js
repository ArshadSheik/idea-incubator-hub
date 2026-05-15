/**
 * bg-fx.js — Hierarchical network with live data flow
 *
 * Three-tier node architecture:
 *   Tier 1 · Hub nodes    (6)  — large, pulsing rings, orange
 *   Tier 2 · Mid nodes   (22)  — medium, violet
 *   Tier 3 · Leaf nodes  (60)  — small, mint/blue
 *
 * Connection rules (dynamic, recomputed as nodes drift):
 *   Hub  ↔ Hub  : thick bright lines, long range
 *   Hub  ↔ Mid  : medium lines
 *   Mid  ↔ Mid  : thin lines, short range
 *   Mid  ↔ Leaf : hair-thin lines, very short range
 *
 * Data packets travel along Hub↔Hub and Hub↔Mid connections —
 * a bright white dot with a fading trail. When it arrives it
 * briefly flares the destination node.
 *
 * Depth layer: three large aurora gradient blobs drift behind
 * the network providing ambient colour wash.
 */
(function () {
  'use strict';

  const canvas = document.getElementById('bgCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W, H, raf, tick = 0;
  let nodes, packets, aurora;

  /* ── Palette ──────────────────────────────────────────────── */
  const C = {
    orange : { r: 255, g:  90, b:  31 },
    violet : { r:  91, g:  63, b: 255 },
    mint   : { r:   0, g: 217, b: 163 },
    pink   : { r: 255, g:  77, b: 143 },
    blue   : { r:  59, g: 130, b: 246 },
    white  : { r: 255, g: 255, b: 255 },
  };

  /* ── Config ───────────────────────────────────────────────── */
  const CFG = {
    hubCount  :  6,
    midCount  : 22,
    leafCount : 60,
    // connection radii
    hubHub    : 600,
    hubMid    : 260,
    midMid    : 160,
    midLeaf   : 110,
    // packets
    maxPackets: 22,
    packetHz  : 18,   // frames between spawn attempts
    // speeds
    hubSpd    : 0.09,
    midSpd    : 0.16,
    leafSpd   : 0.24,
  };

  /* ─────────────────────────────────────────────────────────────
     Node
  ───────────────────────────────────────────────────────────── */
  class Node {
    constructor (tier) {
      this.tier = tier;
      /* scatter nodes across the full canvas with some margin */
      this.x  = 80 + Math.random() * (W - 160);
      this.y  = 80 + Math.random() * (H - 160);
      const ang = Math.random() * Math.PI * 2;
      const spd = tier === 1 ? CFG.hubSpd : tier === 2 ? CFG.midSpd : CFG.leafSpd;
      this.vx = Math.cos(ang) * spd * (0.5 + Math.random() * 0.8);
      this.vy = Math.sin(ang) * spd * (0.5 + Math.random() * 0.8);
      /* wobble offset so each node follows a unique curved path */
      this.wo = Math.random() * Math.PI * 2;
      this.ws = 0.004 + Math.random() * 0.006;
      /* visual */
      this.r  = tier === 1 ? 4.5 : tier === 2 ? 2.2 : 1.1;
      this.c  = tier === 1 ? C.orange : tier === 2 ? C.violet
                           : (Math.random() < 0.5 ? C.mint : C.blue);
      /* (pulse/flare removed — smooth glow only) */
    }

    update () {
      this.wo += this.ws;
      this.vx += Math.cos(this.wo) * 0.003;
      this.vy += Math.sin(this.wo) * 0.003;
      const cap = this.tier === 1 ? 0.13 : this.tier === 2 ? 0.22 : 0.30;
      const s   = Math.hypot(this.vx, this.vy);
      if (s > cap) { this.vx *= 0.97; this.vy *= 0.97; }
      this.x += this.vx;
      this.y += this.vy;
      /* soft wall repulsion keeps nodes on screen */
      const m = 60;
      if (this.x < m)     this.vx += 0.025;
      if (this.x > W - m) this.vx -= 0.025;
      if (this.y < m)     this.vy += 0.025;
      if (this.y > H - m) this.vy -= 0.025;
    }

    draw (alpha, dark) {
      const { r, g, b } = this.c;

      /* smooth glow halo */
      const gr  = this.r * (this.tier === 1 ? 9 : this.tier === 2 ? 7 : 5);
      const grd = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, gr);
      const coreA = alpha * (this.tier === 1 ? 0.55 : 0.38);
      grd.addColorStop(0, `rgba(${r},${g},${b},${Math.min(1, coreA)})`);
      grd.addColorStop(1, `rgba(${r},${g},${b},0)`);
      ctx.beginPath();
      ctx.arc(this.x, this.y, gr, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();

      /* sharp core dot */
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r},${g},${b},${Math.min(1, alpha)})`;
      ctx.fill();
    }
  }

  /* ─────────────────────────────────────────────────────────────
     Packet — travels from nodeA to nodeB along a straight line
  ───────────────────────────────────────────────────────────── */
  class Packet {
    constructor (a, b) {
      this.a     = a;
      this.b     = b;
      this.t     = 0;
      this.speed = 0.005 + Math.random() * 0.007;
      this.trail = [];
    }

    get done () { return this.t >= 1; }

    get pos () {
      return {
        x: this.a.x + (this.b.x - this.a.x) * this.t,
        y: this.a.y + (this.b.y - this.a.y) * this.t,
      };
    }

    update () {
      const p = this.pos;
      this.trail.push({ x: p.x, y: p.y });
      if (this.trail.length > 16) this.trail.shift();
      this.t += this.speed;
      // arrival — no flare
    }

    draw (alpha) {
      const { r, g, b } = C.white;
      const p           = this.pos;

      /* fading tail */
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

      /* head glow */
      const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, 10);
      grd.addColorStop(0, `rgba(${r},${g},${b},${alpha * 0.7})`);
      grd.addColorStop(1, `rgba(${r},${g},${b},0)`);
      ctx.beginPath();
      ctx.arc(p.x, p.y, 10, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();

      /* sharp core */
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
      ctx.fill();
    }
  }

  /* ─────────────────────────────────────────────────────────────
     Aurora depth blob
  ───────────────────────────────────────────────────────────── */
  class Aurora {
    constructor (i) {
      const pos = [{ x: 0.15, y: 0.18 }, { x: 0.85, y: 0.20 }, { x: 0.50, y: 0.84 }][i];
      this.x    = pos.x * W;
      this.y    = pos.y * H;
      this.r    = Math.min(W, H) * (0.38 + i * 0.07);
      this.c    = [C.orange, C.violet, C.mint][i];
      const a   = Math.random() * Math.PI * 2;
      this.vx   = Math.cos(a) * 0.04;
      this.vy   = Math.sin(a) * 0.04;
      this.wo   = Math.random() * Math.PI * 2;
    }
    update () {
      this.wo += 0.0007;
      this.vx += Math.cos(this.wo) * 0.001;
      this.vy += Math.sin(this.wo) * 0.001;
      const s = Math.hypot(this.vx, this.vy);
      if (s > 0.08) { this.vx *= 0.97; this.vy *= 0.97; }
      this.x += this.vx;
      this.y += this.vy;
      const m = this.r * 0.3;
      if (this.x < -m)    this.vx =  Math.abs(this.vx);
      if (this.x > W + m) this.vx = -Math.abs(this.vx);
      if (this.y < -m)    this.vy =  Math.abs(this.vy);
      if (this.y > H + m) this.vy = -Math.abs(this.vy);
    }
    draw (alpha) {
      const { r, g, b } = this.c;
      const grd = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.r);
      grd.addColorStop(0,    `rgba(${r},${g},${b},${alpha})`);
      grd.addColorStop(0.45, `rgba(${r},${g},${b},${(alpha * 0.25).toFixed(3)})`);
      grd.addColorStop(1,    `rgba(${r},${g},${b},0)`);
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();
    }
  }

  /* ─────────────────────────────────────────────────────────────
     Helpers
  ───────────────────────────────────────────────────────────── */
  function isDark () {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  function dist2 (a, b) {
    const dx = a.x - b.x, dy = a.y - b.y;
    return dx * dx + dy * dy;
  }

  function drawEdge (a, b, lineAlpha, lineW, cr, cg, cb) {
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = `rgba(${cr},${cg},${cb},${lineAlpha})`;
    ctx.lineWidth   = lineW;
    ctx.stroke();
  }

  function vignette (dark) {
    const grd = ctx.createRadialGradient(W / 2, H / 2, H * 0.22, W / 2, H / 2, H * 0.92);
    if (dark) { grd.addColorStop(0, 'rgba(0,0,0,0)'); grd.addColorStop(1, 'rgba(0,0,0,0.60)'); }
    else       { grd.addColorStop(0, 'rgba(255,255,255,0)'); grd.addColorStop(1, 'rgba(255,255,255,0.42)'); }
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, W, H);
  }

  function resize () {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function init () {
    const hubs  = Array.from({ length: CFG.hubCount  }, () => new Node(1));
    const mids  = Array.from({ length: CFG.midCount  }, () => new Node(2));
    const leafs = Array.from({ length: CFG.leafCount }, () => new Node(3));
    nodes   = [...hubs, ...mids, ...leafs];
    packets = [];
    aurora  = [0, 1, 2].map(i => new Aurora(i));
    tick    = 0;
  }

  /* ─────────────────────────────────────────────────────────────
     Render loop
  ───────────────────────────────────────────────────────────── */
  function frame () {
    tick++;
    ctx.clearRect(0, 0, W, H);

    const dark        = isDark();
    const auroraA     = dark ? 0.11  : 0.038;
    const nodeA       = dark ? 0.95  : 0.26;
    const lineBaseA   = dark ? 1.0   : 1.0;   // multiplied per-tier
    const packetA     = dark ? 0.95  : 0.45;

    /* buckets for quick iteration */
    const hubs  = nodes.filter(n => n.tier === 1);
    const mids  = nodes.filter(n => n.tier === 2);
    const leafs = nodes.filter(n => n.tier === 3);

    /* ── Layer 1 · Aurora blobs ── */
    for (const a of aurora) { a.update(); a.draw(auroraA); }

    /* ── Layer 2 · Edges (drawn before nodes so nodes sit on top) ── */

    /* Hub ↔ Hub — thick, bright */
    const hubHubR2 = CFG.hubHub * CFG.hubHub;
    for (let i = 0; i < hubs.length; i++) {
      for (let j = i + 1; j < hubs.length; j++) {
        if (dist2(hubs[i], hubs[j]) < hubHubR2) {
          const { r, g, b } = hubs[i].c;
          drawEdge(hubs[i], hubs[j],
            (dark ? 0.30 : 0.10) * lineBaseA, 1.0, r, g, b);
        }
      }
    }

    /* Hub ↔ Mid */
    const hubMidR2 = CFG.hubMid * CFG.hubMid;
    for (const h of hubs) {
      /* connect to nearest 4 mids within radius */
      const near = mids
        .map(m => ({ m, d2: dist2(h, m) }))
        .filter(x => x.d2 < hubMidR2)
        .sort((a, b) => a.d2 - b.d2)
        .slice(0, 4);
      for (const { m } of near) {
        const { r, g, b } = h.c;
        drawEdge(h, m, (dark ? 0.18 : 0.07) * lineBaseA, 0.6, r, g, b);
      }
    }

    /* Mid ↔ Mid */
    const midMidR2 = CFG.midMid * CFG.midMid;
    for (let i = 0; i < mids.length; i++) {
      for (let j = i + 1; j < mids.length; j++) {
        if (dist2(mids[i], mids[j]) < midMidR2) {
          const { r, g, b } = mids[i].c;
          drawEdge(mids[i], mids[j],
            (dark ? 0.10 : 0.04) * lineBaseA, 0.4, r, g, b);
        }
      }
    }

    /* Mid ↔ Leaf */
    const midLeafR2 = CFG.midLeaf * CFG.midLeaf;
    for (const m of mids) {
      const near = leafs
        .map(l => ({ l, d2: dist2(m, l) }))
        .filter(x => x.d2 < midLeafR2)
        .sort((a, b) => a.d2 - b.d2)
        .slice(0, 3);
      for (const { l } of near) {
        const { r, g, b } = l.c;
        drawEdge(m, l, (dark ? 0.07 : 0.025) * lineBaseA, 0.3, r, g, b);
      }
    }

    /* ── Layer 3 · Nodes ── */
    for (const n of nodes) { n.update(); n.draw(nodeA, dark); }

    /* ── Layer 4 · Data packets ── */
    /* Spawn: try every packetHz frames on random hub↔hub or hub↔mid */
    if (tick % CFG.packetHz === 0 && packets.length < CFG.maxPackets) {
      /* pick two hubs that are close enough */
      const eligible = [];
      for (let i = 0; i < hubs.length; i++) {
        for (let j = i + 1; j < hubs.length; j++) {
          if (dist2(hubs[i], hubs[j]) < hubHubR2) eligible.push([hubs[i], hubs[j]]);
        }
        /* hub → random near mid */
        const near = mids.filter(m => dist2(hubs[i], m) < hubMidR2);
        if (near.length) eligible.push([hubs[i], near[Math.floor(Math.random() * near.length)]]);
      }
      if (eligible.length) {
        const [a, b] = eligible[Math.floor(Math.random() * eligible.length)];
        packets.push(new Packet(a, b));
      }
    }

    packets = packets.filter(p => !p.done);
    for (const p of packets) { p.update(); p.draw(packetA); }

    /* ── Layer 5 · Vignette ── */
    vignette(dark);

    raf = requestAnimationFrame(frame);
  }

  /* ─────────────────────────────────────────────────────────────
     Boot
  ───────────────────────────────────────────────────────────── */
  resize();
  init();
  frame();

  window.addEventListener('resize', () => {
    cancelAnimationFrame(raf);
    resize();
    init();
    frame();
  });
})();
