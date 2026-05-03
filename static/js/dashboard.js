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

  // ── Charts ─────────────────────────────────────────────────────
  fetch('/api/chart-data')
    .then(r => r.json())
    .then(data => {
      const stageCtx = document.getElementById('stageChart');
      if (stageCtx && data.by_stage.length) {
        new Chart(stageCtx, {
          type: 'doughnut',
          data: {
            labels: data.by_stage.map(d => d.stage.charAt(0).toUpperCase() + d.stage.slice(1)),
            datasets: [{
              data: data.by_stage.map(d => d.count),
              backgroundColor: ['#6366f1','#f59e0b','#10b981','#3b82f6'],
              borderWidth: 0,
            }]
          },
          options: {
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } } },
            cutout: '65%',
          }
        });
      }

      const weeklyCtx = document.getElementById('weeklyChart');
      if (weeklyCtx && data.weekly.length) {
        new Chart(weeklyCtx, {
          type: 'bar',
          data: {
            labels: data.weekly.map(d => d.date),
            datasets: [{
              label: 'Ideas submitted',
              data:  data.weekly.map(d => d.count),
              backgroundColor: '#6366f1',
              borderRadius: 6,
            }]
          },
          options: {
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: '#f3f4f6' } },
              x: { grid: { display: false } }
            }
          }
        });
      }
    })
  .catch(() => {});
});
