/* profile.js — bookmarks grid on profile */

function escapeHtml(text) {
  if (text == null) return '';
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}

const PSC_CATEGORY_CLASS = {
  FinTech: 'psc-cat--fintech',
  EdTech: 'psc-cat--edtech',
  GreenTech: 'psc-cat--greentech',
  Health: 'psc-cat--health',
  DevTools: 'psc-cat--devtools',
  Productivity: 'psc-cat--productivity',
  Social: 'psc-cat--social',
  'Creator Economy': 'psc-cat--creator',
  Other: 'psc-cat--other',
};

function pscCategoryClass(cat) {
  return PSC_CATEGORY_CLASS[cat] || 'psc-cat--other';
}

function bookmarkCardHtml(idea) {
  const catCls = pscCategoryClass(idea.category);
  const esc = escapeHtml;
  const stageSlug = String(idea.stage_class || 'validation').toLowerCase();
  return `
    <article class="psc-idea-card psc-idea-card--bookmark" data-idea-id="${esc(idea.id)}" data-scroll-reveal>
      <div class="psc-idea-card__shape psc-idea-card__shape--1" aria-hidden="true"></div>
      <div class="psc-idea-card__shape psc-idea-card__shape--2" aria-hidden="true"></div>
      <div class="psc-idea-card__panel">
        <header class="psc-idea-card__head">
          <span class="psc-idea-card__emoji" aria-hidden="true">💡</span>
          <span class="psc-cat ${catCls}">${esc(idea.category)}</span>
          <span class="stage-pill stage-${stageSlug}"><span class="stage-dot"></span>${esc(String(idea.stage))}</span>
        </header>
        <h3 class="psc-idea-card__title">
          <a href="/ideas/${esc(idea.id)}">${esc(idea.title)}</a>
        </h3>
        <p class="psc-idea-card__summary">${esc(idea.summary)}</p>
        <div class="psc-idea-card__row">
          <div class="psc-idea-card__author">
            <span class="avatar avatar-sm ${esc(idea.author.avatar_class)}">${esc(idea.author.initials)}</span>
            <span class="psc-idea-card__author-name">${esc(idea.author.name)}</span>
          </div>
        </div>
        <footer class="psc-idea-card__footer">
          <span class="psc-meta-stat" title="Upvotes"><i class="bi bi-caret-up-fill"></i>${esc(idea.votes)}</span>
          <span class="psc-meta-stat" title="Comments"><i class="bi bi-chat"></i>${esc(idea.comments_total)}</span>
          <span class="psc-meta-stat" title="Collaborators"><i class="bi bi-people"></i>${esc(idea.collaborators_total)}</span>
          <a href="/ideas/${esc(idea.id)}" class="psc-btn-view">View <i class="bi bi-arrow-up-right ms-1"></i></a>
        </footer>
      </div>
    </article>`;
}

document.addEventListener('DOMContentLoaded', () => {
  const bookmarksTab = document.querySelector('[href="#tab-bookmarks"]');
  const bookmarksGrid = document.getElementById('bookmarksGrid');
  let bookmarksLoaded = false;

  if (bookmarksTab && bookmarksGrid) {
    bookmarksTab.addEventListener('shown.bs.tab', () => {
      if (bookmarksLoaded) return;
      bookmarksLoaded = true;

      fetch('/api/profile/bookmarks')
        .then(r => r.json())
        .then((data) => {
          if (!data.ok || !data.bookmarks.length) {
            bookmarksGrid.innerHTML = `
              <div class="col-12">
                <div class="empty-state">
                  <i class="bi bi-bookmark"></i>
                  <p>No bookmarks yet. Hit the bookmark icon on any idea to save it here.</p>
                </div>
              </div>`;
            return;
          }

          bookmarksGrid.innerHTML = `<div class="profile-cards-grid">${data.bookmarks.map(bookmarkCardHtml).join('')}</div>`;
          bookmarksGrid.querySelectorAll('[data-scroll-reveal]').forEach((el) => el.classList.add('fade-up'));
        })
        .catch(() => {
          bookmarksGrid.innerHTML = '<div class="col-12"><p class="text-center text-muted-iih py-4">Could not load bookmarks.</p></div>';
        });
    });
  }
});
