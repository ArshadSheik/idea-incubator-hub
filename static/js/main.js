/* ============================================
   IDEA INCUBATOR HUB — GLOBAL JS
   ============================================ */

/* ─── Dark mode (runs immediately, before DOMContentLoaded) ─── */
(function () {
  const STORAGE_KEY = 'iih-theme';
  function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    try { localStorage.setItem(STORAGE_KEY, t); } catch (e) {}
  }
  function getTheme() {
    try { return localStorage.getItem(STORAGE_KEY) || 'light'; } catch (e) { return 'light'; }
  }
  window.__iihTheme = { apply: applyTheme, get: getTheme };
})();

document.addEventListener('DOMContentLoaded', () => {

  /* ─── Theme toggle ─── */
  const toggleBtn = document.getElementById('themeToggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      window.__iihTheme.apply(current === 'dark' ? 'light' : 'dark');
    });
  }

  /* ─── Navbar: glass on scroll ─── */
  const navbar = document.querySelector('.navbar-iih');
  if (navbar) {
    const onScroll = () => {
      navbar.classList.toggle('is-scrolled', window.scrollY > 20);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ─── Highlight active nav link based on page ─── */
  const currentPage = document.body.dataset.page;
  if (currentPage) {
    document.querySelectorAll('.navbar-iih .nav-link').forEach(link => {
      if (link.dataset.page === currentPage) link.classList.add('active');
    });
  }

  /* ─── Navbar search (client-side) ─── */
  const searchInput = document.querySelector('.navbar-search input');
  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && searchInput.value.trim() !== '') {
        window.location.href = `/explore?q=${encodeURIComponent(searchInput.value.trim())}`;
      }
    });
  }

  /* ─── Avatar dropdown ─── */
  const avatar     = document.querySelector('.navbar-avatar');
  const avatarMenu = document.querySelector('.avatar-dropdown');
  if (avatar && avatarMenu) {
    avatar.addEventListener('click', (e) => {
      e.stopPropagation();
      avatarMenu.classList.toggle('show');
    });
    document.addEventListener('click', (e) => {
      if (!avatarMenu.contains(e.target) && e.target !== avatar) {
        avatarMenu.classList.remove('show');
      }
    });
  }

  /* ─── Stagger reveal on load ─── */
  document.querySelectorAll('[data-reveal]').forEach((el, i) => {
    el.style.animationDelay = `${i * 0.06}s`;
    el.classList.add('fade-up');
  });

  /* ─── Reveal on scroll (Intersection Observer) ─── */
  const scrollRevealEls = document.querySelectorAll('[data-scroll-reveal]');
  if (scrollRevealEls.length) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-up');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
    scrollRevealEls.forEach(el => io.observe(el));
  }

  /* ─── Count-up number animation ─── */
  function animateCount(el) {
    const target   = parseFloat(el.dataset.target || el.textContent.replace(/[^0-9.]/g, ''));
    const duration = parseInt(el.dataset.duration || '1800', 10);
    const suffix   = el.dataset.suffix || '';
    const prefix   = el.dataset.prefix || '';
    const isFloat  = el.dataset.float === 'true';
    const start    = performance.now();
    function easeOutExpo(t) { return t === 1 ? 1 : 1 - Math.pow(2, -10 * t); }
    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const val = target * easeOutExpo(progress);
      el.textContent = prefix + (isFloat ? val.toFixed(1) : Math.floor(val).toLocaleString()) + suffix;
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  const countIO = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCount(entry.target);
        countIO.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  document.querySelectorAll('[data-count]').forEach(el => countIO.observe(el));

  /* ─── Subtle 3D tilt for cards ─── */
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const initTiltEffects = (root = document) => {
    if (prefersReducedMotion) return;
    const tiltCards = root.querySelectorAll(
      '.card-iih:not(.explore-idea-card), .psc-idea-card__panel, .psc-collab-card'
    );
    tiltCards.forEach((card) => {
      if (card.dataset.tiltBound === '1') return;
      card.dataset.tiltBound = '1';
      card.classList.add('fx-tilt-ready');
      let rafId = null;
      const onMove = (e) => {
        const rect = card.getBoundingClientRect();
        const px = (e.clientX - rect.left) / rect.width;
        const py = (e.clientY - rect.top) / rect.height;
        const area = rect.width * rect.height;
        const sizeScale = Math.max(0.08, Math.min(1, 110000 / Math.max(area, 1)));
        const rotateY = (px - 0.5) * (10 * sizeScale);
        const rotateX = (0.5 - py) * (8 * sizeScale);
        const lift = 0.6 + (2.2 * sizeScale);
        const zoom = 1 + (0.004 * sizeScale);
        if (rafId) cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(() => {
          card.style.transform = `perspective(950px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-${lift.toFixed(2)}px) scale(${zoom.toFixed(3)})`;
        });
      };
      const onLeave = () => {
        if (rafId) cancelAnimationFrame(rafId);
        card.style.transform = '';
      };
      card.addEventListener('mousemove', onMove);
      card.addEventListener('mouseleave', onLeave);
    });
  };
  window.initTiltEffects = initTiltEffects;
  initTiltEffects(document);

  /* ─── Float card 3D tilt on landing hero ─── */
  if (!prefersReducedMotion) {
    document.querySelectorAll('.float-card').forEach((card) => {
      card.addEventListener('mouseenter', () => {
        card.style.transition = 'transform 0.25s cubic-bezier(.34,1.56,.64,1)';
      });
      card.addEventListener('mouseleave', () => {
        card.style.transition = 'transform 0.4s cubic-bezier(.4,0,.2,1)';
      });
    });
  }

  /* ─── Toast helper ─── */
  window.showToast = function (message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;pointer-events:none;';
      document.body.appendChild(container);
    }
    const bgColor = type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#3B82F6';
    const toast = document.createElement('div');
    toast.style.cssText = `
      background:${bgColor};color:white;padding:.85rem 1.2rem;
      border-radius:12px;font-size:.9rem;font-weight:500;
      box-shadow:0 12px 32px rgba(0,0,0,.2);pointer-events:auto;
      animation:slideInRight .3s cubic-bezier(.34,1.56,.64,1);max-width:320px;`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = 'fadeOut .3s ease-out forwards';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  };

  /* ─── Inject toast + avatar dropdown animation styles once ─── */
  if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
      @keyframes slideInRight { from { transform:translateX(100%);opacity:0; } to { transform:translateX(0);opacity:1; } }
      @keyframes fadeOut { to { opacity:0;transform:translateX(20px); } }
      .avatar-dropdown {
        position:absolute;top:calc(100% + 10px);right:0;
        border-radius:12px;box-shadow:0 12px 32px rgba(11,11,18,.14);
        min-width:220px;padding:.5rem;
        opacity:0;transform:translateY(-8px) scale(.96);
        pointer-events:none;transition:all .18s ease-out;z-index:1050;
      }
      .avatar-dropdown.show { opacity:1;transform:translateY(0) scale(1);pointer-events:auto; }
      .avatar-dropdown a { display:flex;align-items:center;gap:.6rem;padding:.55rem .8rem;border-radius:8px;font-size:.9rem;font-weight:500; }
      .avatar-dropdown a:hover { background:var(--ink-100);color:var(--ink-900); }
      .avatar-dropdown hr { margin:.4rem 0;border:none;border-top:1px solid var(--ink-200); }
      .avatar-dropdown .menu-head { padding:.5rem .8rem .6rem;border-bottom:1px solid var(--ink-200);margin-bottom:.4rem; }
      .avatar-dropdown .menu-head .name { font-weight:700;color:var(--ink-900);font-size:.92rem; }
      .avatar-dropdown .menu-head .email { font-size:.78rem;color:var(--ink-500); }
    `;
    document.head.appendChild(style);
  }

  /* ─── Ecosystem stats ticker (live feed simulation) ─── */
  const ticker = document.getElementById('ecosystemTicker');
  if (ticker) {
    const events = [
      '🚀 New idea posted: "AI-powered legal assistant"',
      '🤝 3 collaborators joined EdTech project',
      '⭐ "FinTech for teens" hit 200 votes',
      '🧠 AI insights generated for GreenTech idea',
      '💬 12 new comments on trending startup idea',
      '🏆 "TuneCoach" marked as Launched!',
      '📊 FinTech category up 18% this week',
      '🔥 New record: 47 ideas submitted today',
    ];
    let idx = 0;
    function rotateTicker() {
      ticker.style.opacity = '0';
      ticker.style.transform = 'translateY(6px)';
      setTimeout(() => {
        ticker.textContent = events[idx % events.length];
        ticker.style.opacity = '1';
        ticker.style.transform = 'translateY(0)';
        idx++;
      }, 300);
    }
    ticker.style.transition = 'opacity .3s ease, transform .3s ease';
    ticker.textContent = events[0];
    idx = 1;
    setInterval(rotateTicker, 3500);
  }

});

/* ─── Notification bell ─── */
const notifBell     = document.getElementById('notifBell');
const notifDropdown = document.getElementById('notifDropdown');
const notifBadge    = document.getElementById('notifBadge');
const notifList     = document.getElementById('notifList');
const markAllBtn    = document.getElementById('markAllRead');

const NOTIF_ICONS = {
  vote:    { icon: 'bi-caret-up-fill',    cls: 'type-vote'    },
  comment: { icon: 'bi-chat-dots-fill',   cls: 'type-comment' },
  collab:  { icon: 'bi-person-plus-fill', cls: 'type-collab'  },
};

function loadNotifications() {
  if (!notifBell) return;
  fetch('/api/notifications')
    .then(r => r.json())
    .then(data => {
      if (!data.ok) return;
      if (data.unread_count > 0) {
        notifBadge.textContent = data.unread_count > 9 ? '9+' : data.unread_count;
        notifBadge.classList.remove('d-none');
      } else {
        notifBadge.classList.add('d-none');
      }
      if (data.notifications.length === 0) {
        notifList.innerHTML = '<p class="notif-empty">No notifications yet.</p>';
        return;
      }
      notifList.innerHTML = data.notifications.map(n => {
        const iconInfo = NOTIF_ICONS[n.type] || { icon: 'bi-bell', cls: 'type-comment' };
        return `
          <div class="notif-item ${n.is_read ? '' : 'unread'}"
               data-id="${n.id}" data-link="${n.link || '#'}">
            <div class="notif-icon ${iconInfo.cls}">
              <i class="bi ${iconInfo.icon}"></i>
            </div>
            <div>
              <p class="notif-text mb-0">${n.message}</p>
              <p class="notif-time mb-0">${n.created_at}</p>
            </div>
          </div>`;
      }).join('');
      notifList.querySelectorAll('.notif-item').forEach(item => {
        item.addEventListener('click', () => {
          const id   = item.dataset.id;
          const link = item.dataset.link;
          fetch(`/api/notifications/${id}/read`, {
            method: 'POST',
            headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content }
          }).then(() => {
            item.classList.remove('unread');
            loadNotifications();
          });
          if (link && link !== '#') window.location.href = link;
        });
      });
    })
    .catch(() => {});
}

if (notifBell) {
  notifBell.addEventListener('click', (e) => {
    e.stopPropagation();
    notifDropdown.classList.toggle('show');
    if (notifDropdown.classList.contains('show')) loadNotifications();
  });
  document.addEventListener('click', (e) => {
    if (!notifDropdown.contains(e.target) && e.target !== notifBell) {
      notifDropdown.classList.remove('show');
    }
  });
  if (markAllBtn) {
    markAllBtn.addEventListener('click', () => {
      fetch('/api/notifications/read-all', {
        method: 'POST',
        headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content }
      }).then(() => loadNotifications());
    });
  }
  loadNotifications();
}
