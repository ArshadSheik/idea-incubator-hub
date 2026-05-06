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

  // Profile stat pills
  const statButtons = document.querySelectorAll('.profile-stat');
  if (statButtons.length) {
    const profileUsername = document.querySelector('.profile-username')?.textContent?.replace('@', '').trim();
    const followModalEl = document.getElementById('followListModal');
    const followModalTitle = document.getElementById('followListTitle');
    const followListLoading = document.getElementById('followListLoading');
    const followListEmpty = document.getElementById('followListEmpty');
    const followListError = document.getElementById('followListError');
    const followListItems = document.getElementById('followListItems');
    const modal = (followModalEl && window.bootstrap?.Modal) ? new window.bootstrap.Modal(followModalEl) : null;

    const resetFollowModal = () => {
      if (followListLoading) followListLoading.classList.remove('d-none');
      if (followListEmpty) followListEmpty.classList.add('d-none');
      if (followListError) { followListError.classList.add('d-none'); followListError.textContent = ''; }
      if (followListItems) followListItems.innerHTML = '';
    };

    const renderFollowUsers = (users) => {
      if (!followListItems) return;
      followListItems.innerHTML = users.map((u) => `
        <a class="follow-item" href="/profile/${encodeURIComponent(u.username)}">
          <span class="avatar avatar-sm avatar-${u.avatar_color}">${escapeHtml(u.initials)}</span>
          <div class="follow-item__text">
            <div class="follow-item__name">${escapeHtml(u.display_name)}</div>
            <div class="follow-item__handle">@${escapeHtml(u.username)}</div>
          </div>
          <i class="bi bi-chevron-right ms-auto text-muted"></i>
        </a>
      `).join('');
    };

    statButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const kind = btn.dataset.stat;
        if (kind !== 'followers' && kind !== 'following') return;
        if (!profileUsername) return;
        if (!modal) return;

        resetFollowModal();
        if (followModalTitle) followModalTitle.textContent = kind === 'followers' ? 'Followers' : 'Following';
        modal.show();

        fetch(`/api/profile/${encodeURIComponent(profileUsername)}/${kind}`)
          .then((r) => r.json())
          .then((data) => {
            if (followListLoading) followListLoading.classList.add('d-none');
            if (!data.ok) throw new Error('request failed');
            const users = Array.isArray(data.users) ? data.users : [];
            if (!users.length) {
              followListEmpty?.classList.remove('d-none');
              return;
            }
            renderFollowUsers(users);
          })
          .catch(() => {
            if (followListLoading) followListLoading.classList.add('d-none');
            if (followListError) {
              followListError.textContent = 'Could not load list right now.';
              followListError.classList.remove('d-none');
            }
          });
      });
    });
  }
});
