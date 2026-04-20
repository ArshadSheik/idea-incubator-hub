/* ═══════════════════════════════════════════════
   DASHBOARD JS
   ═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ─── Tab filtering for My Ideas ─── */
  const tabs = document.querySelectorAll('#ideaTabs .dash-tab');
  const ideaCards = document.querySelectorAll('.my-idea-card[data-stage]');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const filter = tab.dataset.filter;

      ideaCards.forEach(card => {
        if (filter === 'all' || card.dataset.stage === filter) {
          card.classList.remove('hide');
        } else {
          card.classList.add('hide');
        }
      });
    });
  });

  /* ─── Follow button toggle ─── */
  document.querySelectorAll('.follow-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const isFollowing = btn.classList.contains('following');
      if (isFollowing) {
        btn.classList.remove('following');
        btn.textContent = 'Follow';
      } else {
        btn.classList.add('following');
        btn.innerHTML = '<i class="bi bi-check-lg"></i> Following';
        if (window.showToast) window.showToast('Now following!');
      }
    });
  });
});
