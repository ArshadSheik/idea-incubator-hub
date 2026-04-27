document.addEventListener("DOMContentLoaded", () => {
  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute("content");

  const getIdeaId = () => {
    const match = window.location.pathname.match(/\/ideas\/(\d+)/);
    return match ? match[1] : null;
  };
  const ideaIdForStorage = getIdeaId();
  const savedIdeasStorageKey = "saved_ideas";
  const likeStorageKey = ideaIdForStorage ? `idea:${ideaIdForStorage}:liked_comments` : null;

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

  const readSavedIdeas = () => {
    try {
      const raw = localStorage.getItem(savedIdeasStorageKey);
      const parsed = raw ? JSON.parse(raw) : [];
      return new Set(Array.isArray(parsed) ? parsed.map(String) : []);
    } catch (_) {
      return new Set();
    }
  };

  const writeSavedIdeas = (savedSet) => {
    localStorage.setItem(savedIdeasStorageKey, JSON.stringify(Array.from(savedSet)));
  };

  const setLikeButtonState = (btn, liked, count) => {
    const iconClass = liked ? "bi bi-hand-thumbs-up-fill" : "bi bi-hand-thumbs-up";
    btn.classList.toggle("liked", liked);
    btn.innerHTML = `<i class="${iconClass}"></i> ${count}`;
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
  const saveBtn = document.getElementById("saveBtn");
  const shareBtn = document.getElementById("shareBtn");
  const collaborateBtn = document.getElementById("collaborateBtn");
  const savedIdeas = readSavedIdeas();

  if (saveBtn && ideaIdForStorage) {
    const setSaveState = (saved) => {
      saveBtn.classList.toggle("voted", saved);
      const label = saveBtn.querySelector("span");
      if (label) label.textContent = saved ? "Saved" : "Save";
      const icon = saveBtn.querySelector("i");
      if (icon) {
        icon.className = saved ? "bi bi-bookmark-fill" : "bi bi-bookmark";
      }
    };

    setSaveState(savedIdeas.has(String(ideaIdForStorage)));
    saveBtn.addEventListener("click", () => {
      const key = String(ideaIdForStorage);
      if (savedIdeas.has(key)) {
        savedIdeas.delete(key);
      } else {
        savedIdeas.add(key);
      }
      writeSavedIdeas(savedIdeas);
      setSaveState(savedIdeas.has(key));
    });
  }

  if (shareBtn) {
    shareBtn.addEventListener("click", async () => {
      const shareData = {
        title: document.title,
        text: "Check out this idea on Idea Incubator Hub",
        url: window.location.href,
      };

      try {
        if (navigator.share) {
          await navigator.share(shareData);
        } else {
          await navigator.clipboard.writeText(window.location.href);
          const label = shareBtn.querySelector("span");
          if (label) {
            const prev = label.textContent;
            label.textContent = "Copied link";
            setTimeout(() => {
              label.textContent = prev || "Share";
            }, 1500);
          }
        }
      } catch (error) {
        console.error(error);
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
        collaborateBtn.classList.toggle("voted", payload.collaborating);
        const label = collaborateBtn.querySelector("span");
        if (label) {
          label.textContent = payload.collaborating
            ? "Joined as collaborator"
            : "Join as collaborator";
        }
      } catch (error) {
        console.error(error);
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
      })
      .finally(() => {
        btn.disabled = false;
      });
  });
});
