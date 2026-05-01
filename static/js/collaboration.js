/* ============================================================
   COLLABORATION BOARD — Kanban drag and drop + task CRUD
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const board = document.getElementById('kanbanBoard');
  if (!board) return;

  // ── Add task modal ─────────────────────────────────────────
  const addTaskBtn = document.getElementById('addTaskBtn');
  const saveTaskBtn = document.getElementById('saveTaskBtn');
  const taskModal = new bootstrap.Modal(document.getElementById('taskModal'));

  addTaskBtn.addEventListener('click', () => taskModal.show());

  saveTaskBtn.addEventListener('click', async () => {
    const title = document.getElementById('taskTitle').value.trim();
    if (!title) {
      document.getElementById('taskTitle').classList.add('is-invalid');
      return;
    }

    const payload = {
      title,
      description:  document.getElementById('taskDesc').value.trim(),
      priority:     document.getElementById('taskPriority').value,
      assigned_to:  document.getElementById('taskAssignee').value || null,
      status:       'todo',
    };

    try {
      const resp = await fetch(`/api/ideas/${IDEA_ID}/tasks`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
        body:    JSON.stringify(payload),
      });
      const data = await resp.json();
      if (!data.ok) throw new Error(data.error);
      taskModal.hide();
      window.location.reload(); // simple reload to show new card
    } catch (err) {
      alert('Could not save task: ' + err.message);
    }
  });

  // ── Delete task ────────────────────────────────────────────
  board.addEventListener('click', async (e) => {
    const deleteBtn = e.target.closest('.task-delete-btn');
    if (!deleteBtn) return;
    if (!confirm('Delete this task?')) return;

    const taskId = deleteBtn.dataset.taskId;
    try {
      await fetch(`/api/ideas/${IDEA_ID}/tasks/${taskId}`, {
        method:  'DELETE',
        headers: { 'X-CSRFToken': CSRF_TOKEN },
      });
      deleteBtn.closest('.task-card').remove();
      updateCounts();
    } catch (err) {
      alert('Could not delete task.');
    }
  });

  // ── Drag and drop ──────────────────────────────────────────
  let draggedCard = null;

  board.addEventListener('dragstart', (e) => {
    draggedCard = e.target.closest('.task-card');
    if (!draggedCard) return;
    draggedCard.classList.add('dragging');
  });

  board.addEventListener('dragend', () => {
    if (draggedCard) draggedCard.classList.remove('dragging');
    document.querySelectorAll('.kanban-col').forEach(col => col.classList.remove('drag-over'));
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

    const newStatus = col.dataset.status;
    const taskId    = draggedCard.dataset.taskId;

    col.querySelector('.col-body').appendChild(draggedCard);
    draggedCard.dataset.status = newStatus;
    col.classList.remove('drag-over');
    updateCounts();

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

  // ── Update column counts ───────────────────────────────────
  function updateCounts() {
    ['todo', 'in_progress', 'done'].forEach(status => {
      const body  = document.getElementById(`body-${status}`);
      const count = document.getElementById(`count-${status}`);
      if (body && count) count.textContent = body.querySelectorAll('.task-card').length;
    });
  }
});