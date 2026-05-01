/* profile.js — bookmark/activity AJAX once auth is live */
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
        .then(data => {
          if (!data.ok || data.bookmarks.length === 0) {
            bookmarksGrid.innerHTML = `
              <div class="col-12">
                <div class="empty-state">
                  <i class="bi bi-bookmark"></i>
                  <p>No bookmarks yet. Hit the bookmark icon on any idea to save it here.</p>
                </div>
              </div>`;
            return;
          }

          bookmarksGrid.innerHTML = data.bookmarks.map(idea => `
            <div class="col-md-6">
              <a href="/ideas/${idea.id}" class="idea-card-link">
                <div class="idea-card">
                  <div class="idea-card-header">
                    <span class="idea-tag ${idea.tag_class}">${idea.category}</span>
                    <span class="stage-pill stage-${idea.stage_class}">
                      <span class="stage-dot"></span>${idea.stage}
                    </span>
                  </div>
                  <h3 class="idea-card-title">${idea.title}</h3>
                  <p class="idea-card-summary">${idea.summary}</p>
                  <div class="idea-card-footer">
                    <div class="idea-author">
                      <div class="avatar avatar-xs ${idea.author.avatar_class}">${idea.author.initials}</div>
                      <span>${idea.author.name}</span>
                    </div>
                    <div class="idea-stats">
                      <span><i class="bi bi-caret-up-fill"></i> ${idea.votes}</span>
                      <span><i class="bi bi-chat"></i> ${idea.comments_total}</span>
                    </div>
                  </div>
                </div>
              </a>
            </div>
          `).join('');
        })
        .catch(() => {
          bookmarksGrid.innerHTML = '<div class="col-12"><p class="text-center text-muted-iih py-4">Could not load bookmarks.</p></div>';
        });
    });
  }

  // TODO: load activity tab via AJAX /api/profile/activity once endpoint is built
});