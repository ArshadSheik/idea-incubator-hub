/* ═══════════════════════════════════════════════
   EXPLORE JS — tabs, filters, sort, load-more
   ═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  const searchInput    = document.getElementById('searchInput');
  const categorySelect = document.getElementById('filterCategory');
  const stageSelect    = document.getElementById('filterStage');
  const sortSelect     = document.getElementById('filterSort');
  const tagSelect      = document.getElementById('filterTag');
  const resetBtn       = document.getElementById('resetFilters');
  const grid           = document.getElementById('ideaGrid');
  const countEl        = document.getElementById('resultsCount');
  const emptyState     = document.getElementById('emptyState');
  const loadMoreWrap   = document.getElementById('loadMoreWrap');
  const loadMoreBtn    = document.getElementById('loadMoreBtn');
  const tabBtns        = document.querySelectorAll('.explore-tab-btn');

  let allItems = Array.from(document.querySelectorAll('.idea-item'));
  let currentTab = new URLSearchParams(window.location.search).get('tab') || 'trending';
  let loadMorePage = 2;
  let hasMore = allItems.length >= 12;

  /* ─── Show/hide Load More on initial render ─── */
  if (hasMore) loadMoreWrap.style.display = '';

  /* ─── Tab switching — full page reload with tab param ─── */
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      const params = new URLSearchParams(window.location.search);
      params.set('tab', tab);
      // reset sort/page when switching tabs
      params.delete('sort');
      window.location.href = `${window.location.pathname}?${params.toString()}`;
    });
  });

  /* ─── Client-side filters (search, category, stage within current page load) ─── */
  function applyFilters() {
    const q        = (searchInput ? searchInput.value : '').trim().toLowerCase();
    const category = categorySelect ? categorySelect.value : 'all';
    const stage    = stageSelect ? stageSelect.value : 'all';
    const tag      = tagSelect ? tagSelect.value.toLowerCase() : '';

    let visible = 0;
    allItems.forEach(item => {
      const matchQ   = !q || item.dataset.title.toLowerCase().includes(q) || (item.dataset.category || '').toLowerCase().includes(q);
      const matchCat = category === 'all' || item.dataset.category === category;
      const matchStg = stage === 'all' || item.dataset.stage === stage;
      const matchTag = !tag || (item.dataset.tagClass || '').toLowerCase().includes(tag);
      const show = matchQ && matchCat && matchStg && matchTag;
      item.classList.toggle('hide', !show);
      if (show) visible++;
    });

    if (countEl) countEl.textContent = visible;
    if (emptyState) emptyState.style.display = visible === 0 ? 'block' : 'none';
    if (grid) grid.style.display = visible === 0 ? 'none' : '';
    syncUrlParams();
  }

  function syncUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const q        = (searchInput ? searchInput.value : '').trim();
    const category = categorySelect ? categorySelect.value : 'all';
    const stage    = stageSelect ? stageSelect.value : 'all';
    const sort     = sortSelect ? sortSelect.value : 'trending';
    const tag      = tagSelect ? tagSelect.value : '';

    q        ? params.set('q', q)               : params.delete('q');
    category !== 'all' ? params.set('category', category) : params.delete('category');
    stage !== 'all'    ? params.set('stage', stage)       : params.delete('stage');
    sort !== 'trending' ? params.set('sort', sort)        : params.delete('sort');
    tag    ? params.set('tag', tag)             : params.delete('tag');

    const qs = params.toString();
    window.history.replaceState({}, '', qs ? `${window.location.pathname}?${qs}` : window.location.pathname);
  }

  /* ─── Sort (re-orders DOM within visible items) ─── */
  function applySort() {
    const sort = sortSelect ? sortSelect.value : 'trending';
    const visible = allItems.filter(i => !i.classList.contains('hide'));

    const getVotes = item => {
      const el = item.querySelector('.meta-item strong');
      return el ? (parseInt(el.textContent.replace(/,/g, ''), 10) || 0) : 0;
    };

    if (sort === 'votes') {
      visible.sort((a, b) => getVotes(b) - getVotes(a));
    } else if (sort === 'newest') {
      // retain server order — newest first is already server-sorted
    }
    visible.forEach(item => grid && grid.appendChild(item));
  }

  /* ─── Load More via /api/explore ─── */
  if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', async () => {
      loadMoreBtn.disabled = true;
      loadMoreBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Loading...';

      const params = new URLSearchParams(window.location.search);
      params.set('page', loadMorePage);

      try {
        const res  = await fetch(`/api/explore?${params.toString()}`);
        const data = await res.json();

        data.ideas.forEach((idea, i) => {
          const cell = document.createElement('div');
          cell.className = 'col-md-6 col-lg-4 idea-item explore-grid__cell';
          cell.style.setProperty('--explore-i', allItems.length + i);
          cell.dataset.category = idea.category || '';
          cell.dataset.stage    = idea.stage_class || 'validation';
          cell.dataset.title    = (idea.title || '').toLowerCase();
          cell.dataset.tagClass = idea.tag_class || '';
          cell.innerHTML = `
            <a href="/idea/${idea.id}" class="explore-card-link text-decoration-none">
              <div class="idea-card card-iih explore-idea-card h-100">
                <div class="card-body-iih">
                  <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
                    <span class="tag ${idea.tag_class}">${idea.category}</span>
                    <span class="stage-pill stage-${idea.stage_class}">
                      <span class="stage-dot"></span>${idea.stage}
                    </span>
                  </div>
                  <h3 class="idea-card-title explore-card-title">
                    <span class="explore-card-emoji" aria-hidden="true">${idea.emoji}</span>
                    ${idea.title}
                  </h3>
                  <p class="idea-card-desc">${idea.summary}</p>
                  <div class="idea-card-meta">
                    <div class="meta-item"><i class="bi bi-caret-up-fill text-brand"></i><strong>${idea.votes}</strong></div>
                    <div class="meta-item"><i class="bi bi-chat"></i>${idea.comments_total}</div>
                    <div class="meta-item"><i class="bi bi-people"></i>${idea.collaborators_total}</div>
                  </div>
                  <hr class="divider">
                  <div class="d-flex align-items-center gap-2">
                    <span class="avatar avatar-sm ${idea.author.avatar_class}">${idea.author.initials}</span>
                    <div class="min-w-0">
                      <div class="small fw-semibold text-truncate">${idea.author.name}</div>
                      <div class="small text-muted-iih">${idea.posted}</div>
                    </div>
                  </div>
                </div>
              </div>
            </a>`;
          grid && grid.appendChild(cell);
        });

        allItems = Array.from(document.querySelectorAll('.idea-item'));
        loadMorePage++;
        hasMore = data.has_more;
        if (countEl) countEl.textContent = data.total;

        if (!hasMore) {
          loadMoreWrap.style.display = 'none';
        }
      } catch (e) {
        // silently fail
      } finally {
        loadMoreBtn.disabled = false;
        loadMoreBtn.innerHTML = '<i class="bi bi-arrow-down-circle me-1"></i> Load more ideas';
      }
    });
  }

  /* ─── Event bindings ─── */
  if (searchInput)    searchInput.addEventListener('input', applyFilters);
  if (categorySelect) categorySelect.addEventListener('change', applyFilters);
  if (stageSelect)    stageSelect.addEventListener('change', applyFilters);
  if (tagSelect)      tagSelect.addEventListener('change', applyFilters);
  if (sortSelect)     sortSelect.addEventListener('change', () => { applyFilters(); applySort(); });

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (searchInput)    searchInput.value    = '';
      if (categorySelect) categorySelect.value = 'all';
      if (stageSelect)    stageSelect.value    = 'all';
      if (sortSelect)     sortSelect.value     = 'trending';
      if (tagSelect)      tagSelect.value      = '';
      applyFilters();
      applySort();
    });
  }

  /* ─── Initial render ─── */
  applyFilters();
  applySort();
});
