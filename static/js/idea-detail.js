document.addEventListener("DOMContentLoaded", () => {
  const upvoteBtn = document.getElementById("upvoteBtn");
  const voteCountEl = document.getElementById("voteCount");
  if (upvoteBtn && voteCountEl) {
    upvoteBtn.addEventListener("click", () => {
      const current = parseInt(voteCountEl.textContent, 10);
      if (upvoteBtn.classList.contains("voted")) {
        upvoteBtn.classList.remove("voted");
        voteCountEl.textContent = current - 1;
        upvoteBtn.querySelector("span").textContent = "Upvote";
      } else {
        upvoteBtn.classList.add("voted");
        voteCountEl.textContent = current + 1;
        upvoteBtn.querySelector("span").textContent = "Upvoted";
      }
    });
  }

  const commentForm = document.getElementById("commentForm");
  const commentInput = document.getElementById("commentInput");
  const commentList = document.getElementById("commentList");
  if (commentForm && commentInput && commentList) {
    commentForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = commentInput.value.trim();
      if (!text) {
        commentInput.classList.add("is-invalid");
        return;
      }
      commentInput.classList.remove("is-invalid");

      const commentHTML = `
        <div class="comment">
          <span class="avatar avatar-1">JL</span>
          <div class="flex-grow-1">
            <div class="comment-meta">
              <strong>Jamie Liu</strong>
              <span class="text-muted-iih small">· just now</span>
            </div>
            <p></p>
            <div class="comment-actions">
              <button class="comment-action"><i class="bi bi-hand-thumbs-up"></i> 0</button>
              <button class="comment-action"><i class="bi bi-reply"></i> Reply</button>
            </div>
          </div>
        </div>`;

      const wrapper = document.createElement("div");
      wrapper.innerHTML = commentHTML.trim();
      const newComment = wrapper.firstChild;
      newComment.querySelector("p").textContent = text;
      commentList.insertBefore(newComment, commentList.firstChild);
      commentInput.value = "";
    });
  }

  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".comment-action");
    if (!btn || !btn.querySelector(".bi-hand-thumbs-up")) return;
    e.preventDefault();

    const text = btn.textContent.trim();
    const match = text.match(/(\d+)/);
    const count = match ? parseInt(match[1], 10) : 0;

    if (btn.classList.contains("liked")) {
      btn.classList.remove("liked");
      btn.innerHTML = `<i class="bi bi-hand-thumbs-up"></i> ${count - 1}`;
    } else {
      btn.classList.add("liked");
      btn.innerHTML = `<i class="bi bi-hand-thumbs-up-fill"></i> ${count + 1}`;
    }
  });
});
