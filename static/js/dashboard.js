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

  // ── Stage doughnut chart ─────────────────────────────────────
  fetch('/api/chart-data')
    .then(r => r.json())
    .then(data => {
      const stageCtx = document.getElementById('stageChart');
      if (stageCtx) {
        const stageData = data.by_stage.length
          ? data.by_stage
          : [{ stage: 'No data yet', count: 1 }];
        new Chart(stageCtx, {
          type: 'doughnut',
          data: {
            labels: stageData.map(d => d.stage.charAt(0).toUpperCase() + d.stage.slice(1)),
            datasets: [{
              data: stageData.map(d => d.count),
              backgroundColor: data.by_stage.length
                ? ['#6366f1','#f59e0b','#10b981','#3b82f6']
                : ['#e5e7eb'],
              borderWidth: 0,
            }]
          },
          options: {
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } } },
            cutout: '65%',
          }
        });
      }
    })
    .catch(() => {});

  // ── Vote velocity chart (top idea, last 7 days) ───────────────
  fetch('/api/vote-velocity')
    .then(r => r.json())
    .then(data => {
      const weeklyCtx = document.getElementById('weeklyChart');
      if (!weeklyCtx) return;
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const gridColor = isDark ? 'rgba(255,255,255,0.06)' : '#f3f4f6';
      new Chart(weeklyCtx, {
        type: 'bar',
        data: {
          labels: data.daily.map(d => d.date),
          datasets: [{
            label: 'Votes',
            data: data.daily.map(d => d.count),
            backgroundColor: 'rgba(91,63,255,0.75)',
            hoverBackgroundColor: '#FF5A1F',
            borderRadius: 6,
          }]
        },
        options: {
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, grid: { color: gridColor } },
            x: { grid: { display: false } }
          }
        }
      });
    })
    .catch(() => {});
});
