/* ============================================================
   COLLABORATION BOARD — Kanban drag and drop + task CRUD
   ============================================================ */

function escapeHtml(str) {
  if (str == null) return '';
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}

/* ── Activity helpers ─────────────────────────────────────── */
const ACTION_ICONS  = { created: '✦', moved: '⇒', deleted: '✕', updated: '✎' };
const STATUS_LABELS = { todo: 'To Do', in_progress: 'In Progress', done: 'Done' };

let latestActivityId = null;   // tracks newest server-side ID for polling

function buildActivityItem(entry) {
  const li = document.createElement('li');
  li.className = 'activity-item';
  li.dataset.action = entry.action;
  li.innerHTML = `
    <div class="activity-dot action-${escapeHtml(entry.action)}">
      ${escapeHtml(ACTION_ICONS[entry.action] || '•')}
    </div>
    <div class="activity-body">
      <div class="activity-detail">${escapeHtml(entry.detail)}</div>
      <div class="activity-meta">${escapeHtml(entry.user_name)} · ${escapeHtml(entry.time)}</div>
    </div>`;
  return li;
}

function prependActivity(action, detail) {
  const list  = document.getElementById('activityList');
  const empty = document.getElementById('activityEmpty');
  if (!list) return;

  if (empty) empty.remove();

  const li = buildActivityItem({
    action,
    detail,
    user_name: CURRENT_USER.name,
    time: 'just now',
  });
  li.classList.add('activity-new');
  list.prepend(li);

  // cap displayed list at 20
  const items = list.querySelectorAll('.activity-item');
  if (items.length > 20) items[items.length - 1].remove();
}

async function pollActivity() {
  try {
    const res  = await fetch(`/api/ideas/${IDEA_ID}/board/activity`);
    if (!res.ok) return;
    const data = await res.json();
    if (!data.length) return;

    const newestId = data[0].id;

    // First poll — just record the baseline
    if (latestActivityId === null) {
      latestActivityId = newestId;
      return;
    }

    // Nothing new from other users
    if (newestId === latestActivityId) return;

    // New activity from teammates — replace the whole list
    latestActivityId = newestId;
    const list = document.getElementById('activityList');
    if (!list) return;

    list.innerHTML = '';
    data.forEach(entry => {
      const li = buildActivityItem(entry);
      li.classList.add('activity-flash');
      list.appendChild(li);
    });
  } catch (_) { /* silent */ }
}

/* ── DOMContentLoaded ─────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const board = document.getElementById('kanbanBoard');
  if (!board) return;

  // seed the latest ID from whatever the page already shows
  pollActivity();
  setInterval(pollActivity, 30000);

  /* ── Add task modal (editors only) ───────────────────────── */
  const addTaskBtn  = document.getElementById('addTaskBtn');
  const saveTaskBtn = document.getElementById('saveTaskBtn');
  const taskModalEl = document.getElementById('taskModal');
  const taskModal   = taskModalEl ? new bootstrap.Modal(taskModalEl) : null;

  if (addTaskBtn && taskModal) {
    addTaskBtn.addEventListener('click', () => taskModal.show());
  }

  if (saveTaskBtn && taskModal) saveTaskBtn.addEventListener('click', async () => {
    const titleInput = document.getElementById('taskTitle');
    const title = titleInput.value.trim();
    if (!title) { titleInput.classList.add('is-invalid'); return; }

    const payload = {
      title,
      description: document.getElementById('taskDesc').value.trim(),
      priority:    document.getElementById('taskPriority').value,
      assigned_to: document.getElementById('taskAssignee').value || null,
      status:      'todo',
    };

    try {
      const resp = await fetch(`/api/ideas/${IDEA_ID}/tasks`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
        body:    JSON.stringify(payload),
      });
      const data = await resp.json();
      if (!data.ok) throw new Error(data.error);

      prependActivity('created', `created '${title}'`);
      taskModal.hide();
      window.location.reload();
    } catch (err) {
      alert('Could not save task: ' + err.message);
    }
  });

  /* ── Delete task ──────────────────────────────────────────── */
  board.addEventListener('click', async (e) => {
    const deleteBtn = e.target.closest('.task-delete-btn');
    if (!deleteBtn) return;
    if (!confirm('Delete this task?')) return;

    const taskId   = deleteBtn.dataset.taskId;
    const taskCard = deleteBtn.closest('.task-card');
    const taskTitle = taskCard?.dataset.taskTitle || 'task';

    try {
      const resp = await fetch(`/api/ideas/${IDEA_ID}/tasks/${taskId}`, {
        method:  'DELETE',
        headers: { 'X-CSRFToken': CSRF_TOKEN },
      });
      if (!resp.ok) {
        const d = await resp.json().catch(() => ({}));
        throw new Error(d.error || `HTTP ${resp.status}`);
      }
      prependActivity('deleted', `deleted '${taskTitle}'`);
      taskCard.remove();
      updateCounts();
    } catch (err) {
      alert('Could not delete task: ' + err.message);
    }
  });

  /* ── Accept / Decline collaboration requests (owner; not gated on CAN_EDIT) ─ */
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

  document.addEventListener('click', async (e) => {
    const acceptBtn  = e.target.closest('.accept-collab-btn');
    const declineBtn = e.target.closest('.decline-collab-btn');
    const btn = acceptBtn || declineBtn;
    if (!btn) return;

    const collabId = btn.dataset.collabId;
    const ideaId   = btn.dataset.ideaId;
    const action   = acceptBtn ? 'accept' : 'decline';
    btn.disabled = true;

    try {
      const res  = await fetch(`/ideas/${ideaId}/collaborate/${collabId}/${action}`, {
        method:  'POST',
        headers: { ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}) },
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || 'Request failed');

      document.getElementById(`collabReq-${collabId}`)?.remove();

      if (acceptBtn && data.user_name) {
        const teamList = document.querySelector('.team-list');
        if (teamList) {
          const li = document.createElement('li');
          li.className = 'team-member';
          const avatarNum = escapeHtml(String(data.avatar_class).replace('avatar-', ''));
          li.innerHTML = `
            <div class="avatar avatar-${avatarNum} avatar-sm">${escapeHtml(data.user_initials)}</div>
            <span class="team-member-name">${escapeHtml(data.user_name)}</span>`;
          teamList.querySelector('.text-muted-iih')?.closest('li')?.remove();
          teamList.appendChild(li);
        }
        const teamHeading = document.querySelector('.sidebar-heading');
        if (teamHeading) {
          const count = document.querySelectorAll('.team-member').length;
          teamHeading.innerHTML = `Team <span style="margin-left:.2rem;opacity:.6">(${count})</span>`;
        }
      }

      const remaining = document.querySelectorAll('[id^="collabReq-"]').length;
      if (remaining === 0) document.querySelector('.collab-requests-section')?.remove();

    } catch (err) {
      console.error(err);
      alert('Something went wrong. Please try again.');
      btn.disabled = false;
    }
  });

  /* ── Drag and drop (editors only) ────────────────────────── */
  if (!CAN_EDIT) return;

  let draggedCard = null;

  board.addEventListener('dragstart', (e) => {
    draggedCard = e.target.closest('.task-card');
    if (!draggedCard) return;
    draggedCard.classList.add('dragging');
  });

  board.addEventListener('dragend', () => {
    if (draggedCard) draggedCard.classList.remove('dragging');
    document.querySelectorAll('.kanban-col').forEach(c => c.classList.remove('drag-over'));
    draggedCard = null;
  });

  board.addEventListener('dragover', (e) => {
    e.preventDefault();
    const col = e.target.closest('.kanban-col');
    if (col) {
      document.querySelectorAll('.kanban-col').forEach(c => c.classList.remove('drag-over'));
      col.classList.add('drag-over');
    }
  });

  board.addEventListener('drop', async (e) => {
    e.preventDefault();
    const col = e.target.closest('.kanban-col');
    if (!col || !draggedCard) return;

    const newStatus  = col.dataset.status;
    const oldStatus  = draggedCard.dataset.status;
    const taskId     = draggedCard.dataset.taskId;
    const taskTitle  = draggedCard.dataset.taskTitle || 'task';

    col.querySelector('.col-body').appendChild(draggedCard);
    draggedCard.dataset.status = newStatus;
    col.classList.remove('drag-over');
    updateCounts();

    if (newStatus !== oldStatus) {
      // If the last activity in the list is a move of this same task to oldStatus,
      // this drag is a reversal — remove that entry instead of adding a new one.
      const list = document.getElementById('activityList');
      const lastMoved = list?.querySelector('.activity-item[data-action="moved"]');
      const lastDetail = lastMoved?.querySelector('.activity-detail')?.textContent || '';
      const isUndo = lastMoved &&
                     lastDetail.includes(`'${taskTitle}'`) &&
                     lastDetail.endsWith(`to ${STATUS_LABELS[oldStatus] || oldStatus}`);
      if (isUndo) {
        lastMoved.remove();
      } else {
        prependActivity('moved', `moved '${taskTitle}' to ${STATUS_LABELS[newStatus] || newStatus}`);
      }
    }

    try {
      await fetch(`/api/ideas/${IDEA_ID}/tasks/${taskId}`, {
        method:  'PUT',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
        body:    JSON.stringify({ status: newStatus }),
      });
    } catch (err) {
      console.error('Failed to update task status:', err);
    }
  });

  /* ── Column counts ────────────────────────────────────────── */
  function updateCounts() {
    ['todo', 'in_progress', 'done'].forEach(status => {
      const body  = document.getElementById(`body-${status}`);
      const count = document.getElementById(`count-${status}`);
      if (body && count) count.textContent = body.querySelectorAll('.task-card').length;
    });
  }

});
