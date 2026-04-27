/* ═══════════════════════════════════════════════
   EXPLORE JS — search + filter + sort
   ═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  const searchInput = document.getElementById('searchInput');
  const categorySelect = document.getElementById('filterCategory');
  const stageSelect = document.getElementById('filterStage');
  const sortSelect = document.getElementById('filterSort');
  const resetBtn = document.getElementById('resetFilters');
  const grid = document.getElementById('ideaGrid');
  const countEl = document.getElementById('resultsCount');
  const emptyState = document.getElementById('emptyState');
  const allItems = Array.from(document.querySelectorAll('.idea-item'));

  /* ─── Read URL params on load ─── */
  const urlParams = new URLSearchParams(window.location.search);
  const qParam = urlParams.get('q') || '';
  const categoryParam = urlParams.get('category') || 'all';
  const stageParam = urlParams.get('stage') || 'all';
  const sortParam = urlParams.get('sort') || 'trending';

  searchInput.value = qParam;
  if ([...categorySelect.options].some(opt => opt.value === categoryParam)) {
    categorySelect.value = categoryParam;
  }
  if ([...stageSelect.options].some(opt => opt.value === stageParam)) {
    stageSelect.value = stageParam;
  }
  if ([...sortSelect.options].some(opt => opt.value === sortParam)) {
    sortSelect.value = sortParam;
  }

  function syncUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const q = (searchInput.value || '').trim();
    const category = categorySelect.value;
    const stage = stageSelect.value;
    const sort = sortSelect.value;

    if (q) params.set('q', q); else params.delete('q');
    if (category && category !== 'all') params.set('category', category); else params.delete('category');
    if (stage && stage !== 'all') params.set('stage', stage); else params.delete('stage');
    if (sort && sort !== 'trending') params.set('sort', sort); else params.delete('sort');

    const nextQuery = params.toString();
    const nextUrl = nextQuery ? `${window.location.pathname}?${nextQuery}` : window.location.pathname;
    window.history.replaceState({}, '', nextUrl);
  }

  /* ─── Apply filters ─── */
  function applyFilters() {
    const q = (searchInput.value || '').trim().toLowerCase();
    const category = categorySelect.value;
    const stage = stageSelect.value;

    let visibleCount = 0;

    allItems.forEach(item => {
      const matchesQuery = !q ||
        item.dataset.title.toLowerCase().includes(q) ||
        item.dataset.category.toLowerCase().includes(q);
      const matchesCategory = category === 'all' || item.dataset.category === category;
      const matchesStage = stage === 'all' || item.dataset.stage === stage;

      if (matchesQuery && matchesCategory && matchesStage) {
        item.classList.remove('hide');
        visibleCount++;
      } else {
        item.classList.add('hide');
      }
    });

    countEl.textContent = visibleCount;
    emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
    grid.style.display = visibleCount === 0 ? 'none' : '';
    syncUrlParams();
  }

  /* ─── Apply sort (just re-orders DOM nodes in grid) ─── */
  function applySort() {
    const sort = sortSelect.value;
    const visibleItems = allItems.filter(i => !i.classList.contains('hide'));

    const getVotes = (item) => {
      const voteStrong = item.querySelector('.meta-item strong');
      return voteStrong ? parseInt(voteStrong.textContent.replace(/,/g, ''), 10) : 0;
    };

    const getDate = (item) => {
      // Parse "X days ago" / "X week ago" / etc. — rough sort weights
      const text = (item.querySelector('.text-muted-iih')?.textContent || '').toLowerCase();
      if (text.includes('days')) return parseInt(text, 10) || 1;
      if (text.includes('week'))  return (parseInt(text, 10) || 1) * 7;
      if (text.includes('month')) return (parseInt(text, 10) || 1) * 30;
      return 999;
    };

    if (sort === 'votes') {
      visibleItems.sort((a, b) => getVotes(b) - getVotes(a));
    } else if (sort === 'newest') {
      visibleItems.sort((a, b) => getDate(a) - getDate(b));
    }
    // 'trending' is the default order — leave alone

    visibleItems.forEach(item => grid.appendChild(item));
  }

  /* ─── Event bindings ─── */
  searchInput.addEventListener('input', applyFilters);
  categorySelect.addEventListener('change', applyFilters);
  stageSelect.addEventListener('change', applyFilters);
  sortSelect.addEventListener('change', () => { applyFilters(); applySort(); });

  resetBtn.addEventListener('click', () => {
    searchInput.value = '';
    categorySelect.value = 'all';
    stageSelect.value = 'all';
    sortSelect.value = 'trending';
    applyFilters();
    applySort();
  });

  /* ─── Run once on load ─── */
  applyFilters();
  applySort();
});
