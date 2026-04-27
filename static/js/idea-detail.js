document.addEventListener("DOMContentLoaded", () => {
  const getIdeaId = () => {
    const match = window.location.pathname.match(/\/ideas\/(\d+)/);
    return match ? match[1] : null;
  };
  const ideaIdForStorage = getIdeaId();
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

  const setLikeButtonState = (btn, liked, count) => {
    const iconClass = liked ? "bi bi-hand-thumbs-up-fill" : "bi bi-hand-thumbs-up";
    btn.classList.toggle("liked", liked);
    btn.innerHTML = `<i class="${iconClass}"></i> ${count}`;
  };

  const upvoteBtn = document.getElementById("upvoteBtn");
  const voteCountEl = document.getElementById("voteCount");
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
          },
          body: JSON.stringify({ text }),
        });

        const payload = await response.json();
        if (!response.ok || !payload.ok) {
          throw new Error(payload.error || `Comment request failed: ${response.status}`);
        }

        const comment = payload.comment;
        const commentHTML = `
          <div class="comment">
            <span class="avatar ${comment.avatar_class}">${comment.initials}</span>
            <div class="flex-grow-1">
              <div class="comment-meta">
                <strong>${comment.name}</strong>
                <span class="text-muted-iih small">· ${comment.time}</span>
              </div>
              <p></p>
              <div class="comment-actions">
                <button class="comment-action comment-like-btn" data-comment-id="${comment.id}"><i class="bi bi-hand-thumbs-up"></i> ${comment.likes}</button>
                <button class="comment-action"><i class="bi bi-reply"></i> Reply</button>
              </div>
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
