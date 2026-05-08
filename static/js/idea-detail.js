document.addEventListener("DOMContentLoaded", () => {
  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute("content");

  const getIdeaId = () => {
    const match = window.location.pathname.match(/\/ideas\/(\d+)/);
    return match ? match[1] : null;
  };
  const ideaIdForStorage = getIdeaId();
  const likeStorageKey = ideaIdForStorage ? `idea:${ideaIdForStorage}:liked_comments` : null;
  const aiInsightsStorageKey = ideaIdForStorage ? `idea:${ideaIdForStorage}:ai_insights` : null;
  const actionFeedbackEl = document.getElementById("actionFeedback");
  let feedbackTimer = null;

  const readLikedComments = () => {
    if (!likeStorageKey) return new Set();
    try {
      const raw = localStorage.getItem(likeStorageKey);
      const parsed = raw ? JSON.parse(raw) : [];
      return new Set(Array.isArray(parsed) ? parsed.map(String) : []);
    } catch (_) {
      return new Set();
    }
  };

  const writeLikedComments = (likedSet) => {
    if (!likeStorageKey) return;
    localStorage.setItem(likeStorageKey, JSON.stringify(Array.from(likedSet)));
  };

  const readAiInsightsCache = () => {
    if (!aiInsightsStorageKey) return null;
    try {
      const raw = localStorage.getItem(aiInsightsStorageKey);
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  };

  const writeAiInsightsCache = (insights) => {
    if (!aiInsightsStorageKey) return;
    localStorage.setItem(aiInsightsStorageKey, JSON.stringify(insights));
  };

  const setLikeButtonState = (btn, liked, count) => {
    const iconClass = liked ? "bi bi-hand-thumbs-up-fill" : "bi bi-hand-thumbs-up";
    btn.classList.toggle("liked", liked);
    btn.innerHTML = `<i class="${iconClass}"></i> ${count}`;
  };

  const showActionFeedback = (message, variant = "danger") => {
    if (!actionFeedbackEl) return;
    actionFeedbackEl.textContent = message;
    actionFeedbackEl.classList.remove("d-none", "alert-danger", "alert-success", "alert-info");
    actionFeedbackEl.classList.add(`alert-${variant}`);
    if (feedbackTimer) {
      clearTimeout(feedbackTimer);
    }
    feedbackTimer = setTimeout(() => {
      actionFeedbackEl.classList.add("d-none");
    }, 3500);
  };

  const buildReplyNode = (reply) => {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = `
      <div class="comment ms-4 mt-2" data-comment-id="${reply.id}">
        <span class="avatar ${reply.avatar_class}">${reply.initials}</span>
        <div class="flex-grow-1">
          <div class="comment-meta">
            <strong>${reply.name}</strong>
            <span class="text-muted-iih small">· ${reply.time}</span>
          </div>
          <p></p>
          <div class="comment-actions">
            <button class="comment-action comment-like-btn" data-comment-id="${reply.id}"><i class="bi bi-hand-thumbs-up"></i> ${reply.likes}</button>
          </div>
        </div>
      </div>
    `.trim();
    const node = wrapper.firstChild;
    node.querySelector("p").textContent = reply.text;
    return node;
  };

  const ensureReplyList = (commentContainer, commentId) => {
    let replyList = commentContainer.querySelector(`[data-reply-list-for="${commentId}"]`);
    if (!replyList) {
      replyList = document.createElement("div");
      replyList.className = "reply-list mt-2";
      replyList.dataset.replyListFor = String(commentId);
      commentContainer.querySelector(".flex-grow-1")?.appendChild(replyList);
    }
    return replyList;
  };

  const upvoteBtn = document.getElementById("upvoteBtn");
  const voteCountEl = document.getElementById("voteCount");
  const bookmarkBtn = document.getElementById("bookmarkBtn");
  const bookmarkIcon = document.getElementById("bookmarkIcon");
  const bookmarkLabel = document.getElementById("bookmarkLabel");
  const shareBtn = document.getElementById("shareBtn");
  const collaborateBtn = document.getElementById("collaborateBtn");
  const aiInsightsBtn = document.getElementById("aiInsightsBtn");
  const aiInsightsLoading = document.getElementById("aiInsightsLoading");
  const aiInsightsError = document.getElementById("aiInsightsError");
  const aiInsightsCard = document.getElementById("aiInsightsCard");
  const aiSummaryText = document.getElementById("aiSummaryText");
  const aiStrengthsList = document.getElementById("aiStrengthsList");
  const aiSuggestionsList = document.getElementById("aiSuggestionsList");
  const aiDownloadBtn = document.getElementById("aiDownloadBtn");
  const stageSelect = document.getElementById("stageSelect");
  const saveStageBtn = document.getElementById("saveStageBtn");
  const timelineTrack = document.getElementById("ideaTimelineTrack");
  const ideaStagePill = document.getElementById("ideaStagePill");
  const ideaStageLabel = document.getElementById("ideaStageLabel");
  let currentAiInsights = readAiInsightsCache();

  const renderAiInsights = (insights) => {
    if (!insights) return;
    if (aiSummaryText) aiSummaryText.textContent = insights.summary || "No summary available.";
    if (aiStrengthsList) {
      aiStrengthsList.innerHTML = "";
      (insights.strengths || []).forEach((item) => {
        const li = document.createElement("li");
        li.textContent = item;
        aiStrengthsList.appendChild(li);
      });
    }
    if (aiSuggestionsList) {
      aiSuggestionsList.innerHTML = "";
      (insights.suggestions || []).forEach((item) => {
        const li = document.createElement("li");
        li.textContent = item;
        aiSuggestionsList.appendChild(li);
      });
    }
    aiInsightsCard?.classList.remove("d-none");
    aiDownloadBtn?.classList.remove("d-none");
  };

  const buildInsightsText = (insights) => {
    const strengths = (insights.strengths || []).map((s) => `- ${s}`).join("\n");
    const suggestions = (insights.suggestions || []).map((s) => `- ${s}`).join("\n");
    return [
      "AI Insights",
      "",
      "Summary",
      insights.summary || "",
      "",
      "Strengths",
      strengths || "-",
      "",
      "Suggestions",
      suggestions || "-",
      "",
      `Source: ${window.location.href}`,
    ].join("\n");
  };

  if (currentAiInsights) {
    renderAiInsights(currentAiInsights);
    if (aiInsightsBtn) {
      aiInsightsBtn.classList.add("voted");
      const text = aiInsightsBtn.querySelector("span");
      if (text) {
        text.textContent = "Insights ready";
      } else {
        aiInsightsBtn.innerHTML = `<i class="bi bi-stars"></i> Insights ready`;
      }
    }
  }

  if (aiDownloadBtn) {
    aiDownloadBtn.addEventListener("click", () => {
      if (!currentAiInsights || !ideaIdForStorage) return;
      const blob = new Blob([buildInsightsText(currentAiInsights)], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `idea-${ideaIdForStorage}-ai-insights.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    });
  }

  if (aiInsightsBtn) {
    aiInsightsBtn.addEventListener("click", async () => {
      const ideaId = getIdeaId();
      if (!ideaId) return;

      if (currentAiInsights) {
        renderAiInsights(currentAiInsights);
        showActionFeedback("AI insights already generated. You can download them directly.", "info");
        return;
      }

      aiInsightsBtn.disabled = true;
      aiInsightsLoading?.classList.remove("d-none");
      aiInsightsError?.classList.add("d-none");
      aiInsightsCard?.classList.add("d-none");
      try {
        const response = await fetch(`/ideas/${ideaId}/ai-insights`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
          },
        });
        const payload = await response.json();
        if (!response.ok || !payload.ok) {
          throw new Error(payload.error || `AI insight request failed: ${response.status}`);
        }

        currentAiInsights = payload.insights || {};
        writeAiInsightsCache(currentAiInsights);
        renderAiInsights(currentAiInsights);
        aiInsightsBtn.classList.add("voted");
        aiInsightsBtn.innerHTML = `<i class="bi bi-stars"></i> Insights ready`;
      } catch (error) {
        console.error(error);
        if (aiInsightsError) {
          aiInsightsError.textContent = "Unable to generate AI insights right now. Please try again.";
          aiInsightsError.classList.remove("d-none");
        }
      } finally {
        aiInsightsLoading?.classList.add("d-none");
        aiInsightsBtn.disabled = false;
      }
    });
  }

  if (stageSelect && saveStageBtn) {
    saveStageBtn.addEventListener("click", async () => {
      const ideaId = getIdeaId();
      if (!ideaId) return;
      const nextStage = (stageSelect.value || "").trim().toLowerCase();
      if (!nextStage) return;

      saveStageBtn.disabled = true;
      try {
        const response = await fetch(`/ideas/${ideaId}/stage`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
          },
          body: JSON.stringify({ stage: nextStage }),
        });
        const payload = await response.json();
        if (!response.ok || !payload.ok) {
          throw new Error(payload.error || `Stage update failed: ${response.status}`);
        }

        if (ideaStagePill) {
          ideaStagePill.className = `stage-pill stage-${payload.stage_class}`;
          const dot = document.createElement("span");
          dot.className = "stage-dot";
          ideaStagePill.innerHTML = "";
          ideaStagePill.appendChild(dot);
          if (ideaStageLabel) {
            ideaStageLabel.textContent = payload.stage;
            ideaStagePill.appendChild(ideaStageLabel);
          } else {
            const label = document.createElement("span");
            label.textContent = payload.stage;
            ideaStagePill.appendChild(label);
          }
        }

        if (timelineTrack && Array.isArray(payload.stage_timeline)) {
          payload.stage_timeline.forEach((item) => {
            const step = timelineTrack.querySelector(`[data-stage-key="${item.key}"]`);
            if (!step) return;
            step.classList.remove("timeline-step-completed", "timeline-step-active", "timeline-step-upcoming");
            step.classList.add(`timeline-step-${item.state}`);
          });
        }

        showActionFeedback("Progress stage updated.", "success");
      } catch (error) {
        console.error(error);
        showActionFeedback("Unable to update stage right now. Please try again.");
      } finally {
        saveStageBtn.disabled = false;
      }
    });
  }

  if (bookmarkBtn && ideaIdForStorage) {
    const setBookmarkState = (bookmarked) => {
      bookmarkBtn.classList.toggle("voted", bookmarked);
      if (bookmarkIcon) {
        bookmarkIcon.className = bookmarked ? "bi bi-bookmark-fill" : "bi bi-bookmark";
      }
      if (bookmarkLabel) {
        bookmarkLabel.textContent = bookmarked ? "Bookmarked" : "Bookmark";
      }
    };

    const loadBookmarkState = async () => {
      try {
        const response = await fetch(`/api/ideas/${ideaIdForStorage}/bookmark-status`);
        const payload = await response.json();
        if (response.ok && payload.ok) {
          setBookmarkState(Boolean(payload.bookmarked));
        }
      } catch (error) {
        console.error(error);
      }
    };

    loadBookmarkState();
    bookmarkBtn.addEventListener("click", async () => {
      bookmarkBtn.disabled = true;
      try {
        const response = await fetch(`/api/ideas/${ideaIdForStorage}/bookmark`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
          },
        });
        const payload = await response.json();
        if (!response.ok || !payload.ok) {
          throw new Error(payload.error || `Bookmark request failed: ${response.status}`);
        }
        const bookmarked = Boolean(payload.bookmarked);
        setBookmarkState(bookmarked);
      } catch (error) {
        console.error(error);
        showActionFeedback("Unable to update bookmark right now. Please try again.");
      } finally {
        bookmarkBtn.disabled = false;
      }
    });
  }

  if (collaborateBtn) {
    collaborateBtn.addEventListener("click", async () => {
      const ideaId = getIdeaId();
      if (!ideaId) return;
      collaborateBtn.disabled = true;
      try {
        const response = await fetch(`/ideas/${ideaId}/collaborate`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
          },
        });
        const payload = await response.json();
        if (!response.ok || !payload.ok) {
          throw new Error(payload.error || `Collaborate request failed: ${response.status}`);
        }

        // Update button state
        collaborateBtn.classList.toggle("voted", payload.collaborating);
        const label = collaborateBtn.querySelector("span");
        if (label) {
          label.textContent = payload.collaborating
            ? "Joined as collaborator"
            : "Join as collaborator";
        }

        // Update sidebar count heading
        const countEl = document.querySelector(".sidebar-card .collab-list")
          ?.closest(".sidebar-card")
          ?.querySelector(".text-muted-iih.small");
        if (countEl) {
          countEl.textContent = `(${payload.collaborators_total})`;
        }

        // Re-render collaborator list
        const collabList = document.querySelector(".collab-list");
        if (collabList && payload.collaborators) {
          collabList.innerHTML = payload.collaborators
            .map(
              (m) => `
            <div class="collab-item">
              <span class="avatar avatar-sm ${m.avatar_class}">${m.initials}</span>
              <div><strong>${m.name}</strong><span>${m.role}</span></div>
            </div>`
            )
            .join("");
        }

      } catch (error) {
        console.error(error);
        showActionFeedback("Unable to update collaboration right now. Please try again.");
      } finally {
        collaborateBtn.disabled = false;
      }
    });
  }

  if (upvoteBtn && voteCountEl) {
    upvoteBtn.addEventListener("click", async () => {
      const ideaId = getIdeaId();
      if (!ideaId) return;
      upvoteBtn.disabled = true;
      try {
        const response = await fetch(`/ideas/${ideaId}/vote`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
          },
        });

        if (!response.ok) {
          throw new Error(`Vote request failed: ${response.status}`);
        }

        const payload = await response.json();
        voteCountEl.textContent = payload.vote_count;
        if (payload.voted) {
          upvoteBtn.classList.add("voted");
          upvoteBtn.querySelector("span").textContent = "Upvoted";
        } else {
          upvoteBtn.classList.remove("voted");
          upvoteBtn.querySelector("span").textContent = "Upvote";
        }
      } catch (error) {
        console.error(error);
        showActionFeedback("Unable to update vote right now. Please try again.");
      } finally {
        upvoteBtn.disabled = false;
      }
    });
  }

  const commentForm = document.getElementById("commentForm");
  const commentInput = document.getElementById("commentInput");
  const commentList = document.getElementById("commentList");
  const likedComments = readLikedComments();
  const existingLikeButtons = document.querySelectorAll(".comment-like-btn");
  existingLikeButtons.forEach((btn) => {
    const commentId = btn.dataset.commentId;
    if (!commentId) return;
    if (likedComments.has(String(commentId))) {
      const text = btn.textContent.trim();
      const match = text.match(/(\d+)/);
      const count = match ? parseInt(match[1], 10) : 0;
      setLikeButtonState(btn, true, count);
    }
  });

  if (commentForm && commentInput && commentList) {
    commentForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const ideaId = getIdeaId();
      if (!ideaId) return;

      const text = commentInput.value.trim();
      if (!text) {
        commentInput.classList.add("is-invalid");
        showActionFeedback("Comment cannot be empty. Please enter some text.", "info");
        return;
      }
      commentInput.classList.remove("is-invalid");
      const submitBtn = commentForm.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;
      try {
        const response = await fetch(`/ideas/${ideaId}/comments`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
          },
          body: JSON.stringify({ text }),
        });

        const payload = await response.json();
        if (!response.ok || !payload.ok) {
          throw new Error(payload.error || `Comment request failed: ${response.status}`);
        }

        const comment = payload.comment;
        const commentHTML = `
          <div class="comment" data-comment-id="${comment.id}">
            <span class="avatar ${comment.avatar_class}">${comment.initials}</span>
            <div class="flex-grow-1">
              <div class="comment-meta">
                <strong>${comment.name}</strong>
                <span class="text-muted-iih small">· ${comment.time}</span>
              </div>
              <p></p>
              <div class="comment-actions">
                <button class="comment-action comment-like-btn" data-comment-id="${comment.id}"><i class="bi bi-hand-thumbs-up"></i> ${comment.likes}</button>
                <button class="comment-action comment-reply-btn" data-comment-id="${comment.id}"><i class="bi bi-reply"></i> Reply</button>
              </div>
              <div class="reply-list mt-2" data-reply-list-for="${comment.id}"></div>
            </div>
          </div>`;

        const wrapper = document.createElement("div");
        wrapper.innerHTML = commentHTML.trim();
        const newComment = wrapper.firstChild;
        newComment.querySelector("p").textContent = comment.text;
        commentList.insertBefore(newComment, commentList.firstChild);
        commentInput.value = "";
      } catch (error) {
        console.error(error);
        showActionFeedback("Unable to post comment. Please try again.");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  document.addEventListener("click", (e) => {
    const replyBtn = e.target.closest(".comment-reply-btn");
    if (!replyBtn) return;
    e.preventDefault();
    const ideaId = getIdeaId();
    const commentId = replyBtn.dataset.commentId;
    const commentContainer = replyBtn.closest(".comment[data-comment-id]");
    if (!ideaId || !commentId || !commentContainer) return;

    const existingComposer = commentContainer.querySelector(".reply-composer");
    if (existingComposer) {
      existingComposer.remove();
      return;
    }

    const composer = document.createElement("div");
    composer.className = "reply-composer mt-2";
    composer.innerHTML = `
      <textarea class="form-control-iih" rows="2" placeholder="Write a reply..."></textarea>
      <div class="d-flex justify-content-end gap-2 mt-2">
        <button type="button" class="btn btn-outline-iih btn-sm-iih reply-cancel-btn">Cancel</button>
        <button type="button" class="btn btn-brand btn-sm-iih reply-submit-btn">Reply</button>
      </div>
    `;

    const contentWrap = commentContainer.querySelector(".flex-grow-1");
    const replyList = ensureReplyList(commentContainer, commentId);
    contentWrap?.insertBefore(composer, replyList);

    const textarea = composer.querySelector("textarea");
    const submitBtn = composer.querySelector(".reply-submit-btn");
    const cancelBtn = composer.querySelector(".reply-cancel-btn");
    textarea?.focus();

    cancelBtn?.addEventListener("click", () => composer.remove());
    submitBtn?.addEventListener("click", async () => {
      const text = (textarea?.value || "").trim();
      if (!text) {
        textarea?.classList.add("is-invalid");
        showActionFeedback("Reply cannot be empty. Please enter some text.", "info");
        return;
      }
      textarea?.classList.remove("is-invalid");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const response = await fetch(`/ideas/${ideaId}/comments/${commentId}/replies`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
          },
          body: JSON.stringify({ text }),
        });

        const payload = await response.json();
        if (!response.ok || !payload.ok) {
          throw new Error(payload.error || `Reply request failed: ${response.status}`);
        }

        const replyNode = buildReplyNode(payload.reply);
        const targetReplyList = ensureReplyList(commentContainer, commentId);
        targetReplyList.insertBefore(replyNode, targetReplyList.firstChild);
        composer.remove();
      } catch (error) {
        console.error(error);
        showActionFeedback("Unable to post reply. Please try again.");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  });

  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".comment-like-btn");
    if (!btn) return;
    e.preventDefault();
    const ideaId = getIdeaId();
    const commentId = btn.dataset.commentId;
    if (!ideaId || !commentId) return;

    const text = btn.textContent.trim();
    const countMatch = text.match(/(\d+)/);
    const count = countMatch ? parseInt(countMatch[1], 10) : 0;
    const currentlyLiked = btn.classList.contains("liked");
    const action = currentlyLiked ? "unlike" : "like";

    btn.disabled = true;
    fetch(`/ideas/${ideaId}/comments/${commentId}/like`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      },
      body: JSON.stringify({
        action,
        currently_liked: currentlyLiked,
      }),
    })
      .then(async (response) => {
        const payload = await response.json();
        if (!response.ok || !payload.ok) {
          throw new Error(payload.error || `Comment like failed: ${response.status}`);
        }
        setLikeButtonState(btn, payload.liked, payload.like_count);
        if (payload.liked) {
          likedComments.add(String(commentId));
        } else {
          likedComments.delete(String(commentId));
        }
        writeLikedComments(likedComments);
      })
      .catch((error) => {
        console.error(error);
        // Keep UI unchanged on error.
        setLikeButtonState(btn, currentlyLiked, count);
        showActionFeedback("Unable to update comment like right now. Please try again.");
      })
      .finally(() => {
        btn.disabled = false;
      });
  });

  // ── Market News ────────────────────────────────────────────────
  (function loadMarketNews() {
    const container = document.getElementById('newsContent');
    if (!container) return;

    // Uses getIdeaId() — already defined at top of this file
    const ideaId = getIdeaId();
    if (!ideaId) return;

    fetch(`/api/ideas/${ideaId}/news`)
      .then(r => r.json())
      .then(data => {
        if (!data.ok || !data.articles.length) {
          container.innerHTML = '<p class="text-muted-iih small text-center py-2">No recent news found.</p>';
          return;
        }
        container.innerHTML = data.articles.slice(0, 4).map(a => `
          <a href="${a.url}" target="_blank" rel="noopener" class="news-item">
            <p class="news-title mb-0">${a.title}</p>
            <span class="news-meta">${a.source} · ${new Date(a.published_at).toLocaleDateString()}</span>
          </a>
        `).join('');
      })
      .catch(() => {
        container.innerHTML = '<p class="text-muted-iih small text-center py-2">Could not load news.</p>';
      });
  })();

  // ── Wikipedia category context ─────────────────────────────────
  (function loadWikipediaContext() {
    const wikiText    = document.getElementById('wikiText');
    const wikiLink    = document.getElementById('wikiLink');
    const wikiToggle  = document.getElementById('wikiToggle');
    const wikiContent = document.getElementById('wikiContent');
    if (!wikiText) return;

    const WIKI_TOPICS = {
      'FinTech':         'Financial_technology',
      'EdTech':          'Educational_technology',
      'GreenTech':       'Green_technology',
      'Health':          'Health_technology',
      'DevTools':        'Programming_tool',
      'Productivity':    'Productivity_software',
      'Social':          'Social_media',
      'Creator Economy': 'Creator_economy',
      'Other':           'Startup_company',
    };

    const category = document.body.dataset.ideaCategory || 'Other';
    const topic    = WIKI_TOPICS[category] || 'Startup_company';

    fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${topic}`)
      .then(r => r.json())
      .then(data => {
        wikiText.textContent = data.extract
          ? data.extract.split('.').slice(0, 2).join('.') + '.'
          : 'No summary available.';
        if (data.content_urls?.desktop?.page) {
          wikiLink.href = data.content_urls.desktop.page;
          wikiLink.classList.remove('d-none');
        }
      })
      .catch(() => { wikiText.textContent = 'Could not load context.'; });

    if (wikiToggle) {
      wikiToggle.addEventListener('click', () => {
        wikiContent.classList.toggle('collapsed');
        wikiToggle.querySelector('i').className =
          wikiContent.classList.contains('collapsed') ? 'bi bi-chevron-right' : 'bi bi-chevron-down';
      });
    }
  })();

  (function () {
    const modal      = document.getElementById('shareModal');
    const openBtn    = document.getElementById('shareBtn');
    const closeBtn   = document.getElementById('shareModalClose');
    const copyBtn    = document.getElementById('shareCopyBtn');
    const copyIcon   = document.getElementById('shareCopyIcon');
    const copyLabel  = document.getElementById('shareCopyLabel');
    const linkInput  = document.getElementById('shareLinkInput');
    const toast      = document.getElementById('shareToast');

    if (!modal || !openBtn) return;

    const pageUrl   = linkInput.value;
    const ideaTitle = document.querySelector('h1')?.textContent?.trim() || 'Check out this idea';
    const summary   = document.querySelector('.idea-section p')?.textContent?.trim()?.slice(0, 120) || '';

    // ── Open / Close ──────────────────────────────────────────────
    function openModal() {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
      buildShareLinks();
    }

    function closeModal() {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }

    openBtn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

    // ── Build share URLs ──────────────────────────────────────────
    function buildShareLinks() {
      const encoded  = encodeURIComponent(pageUrl);
      const encTitle = encodeURIComponent(ideaTitle);
      const encText  = encodeURIComponent(`${ideaTitle} — ${summary}`);

      document.getElementById('shareTwitter').href =
        `https://twitter.com/intent/tweet?url=${encoded}&text=${encText}`;

      document.getElementById('shareLinkedin').href =
        `https://www.linkedin.com/sharing/share-offsite/?url=${encoded}`;

      document.getElementById('shareFacebook').href =
        `https://www.facebook.com/sharer/sharer.php?u=${encoded}`;

      document.getElementById('shareReddit').href =
        `https://reddit.com/submit?url=${encoded}&title=${encTitle}`;

      document.getElementById('shareWhatsapp').href =
        `https://wa.me/?text=${encText}%20${encoded}`;

      document.getElementById('shareEmail').addEventListener('click', () => {
        window.location.href =
          `mailto:?subject=${encTitle}&body=${encodeURIComponent(summary + '\n\n' + pageUrl)}`;
      });
    }

    // ── Copy link ─────────────────────────────────────────────────
    copyBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(pageUrl);
      } catch {
        // fallback for older browsers
        linkInput.select();
        document.execCommand('copy');
      }
      // Update button state
      copyIcon.className  = 'bi bi-clipboard-check';
      copyLabel.textContent = 'Copied!';
      copyBtn.style.background = 'var(--color-success, #22c55e)';

      // Show toast
      toast.classList.remove('d-none');
      toast.classList.add('show');

      setTimeout(() => {
        copyIcon.className  = 'bi bi-clipboard';
        copyLabel.textContent = 'Copy';
        copyBtn.style.background = '';
        toast.classList.remove('show');
        setTimeout(() => toast.classList.add('d-none'), 300);
      }, 2000);
    });
    
  })();

  // ── Trending Hashtags ──────────────────────────────────────────
  (function loadTrendingHashtags() {
    const container = document.getElementById('hashtagContent');
    if (!container) return;

    fetch('/api/trending-hashtags')
      .then(r => r.json())
      .then(data => {
        if (!data.length) {
          container.innerHTML = '<p class="text-muted-iih small text-center py-2">No trending tags yet.</p>';
          return;
        }

        // 최대값 기준으로 bar 너비 계산
        const maxTotal = Math.max(...data.map(d => d.total), 1);

        container.innerHTML = data.map((item, i) => {
          const barWidth = Math.round((item.total / maxTotal) * 100);
          const isHot    = item.recent > 0;
          const rankIcon = i === 0 ? '🔥' : i === 1 ? '⚡' : i === 2 ? '✨' : '#';

          return `
            <a href="/explore?tag=${encodeURIComponent(item.tag)}"
              class="hashtag-item text-decoration-none"
              title="${item.total} ideas · ${item.recent} this week">
              <div class="hashtag-top">
                <span class="hashtag-rank">${rankIcon}</span>
                <span class="hashtag-name">#${item.tag}</span>
                ${isHot ? '<span class="hashtag-hot">NEW</span>' : ''}
                <span class="hashtag-count ms-auto">${item.total}</span>
              </div>
              <div class="hashtag-bar-track">
                <div class="hashtag-bar-fill" style="width: ${barWidth}%"></div>
              </div>
            </a>
          `;
        }).join('');
      })
      .catch(() => {
        container.innerHTML = '<p class="text-muted-iih small text-center py-2">Could not load hashtags.</p>';
      });
  })();


});