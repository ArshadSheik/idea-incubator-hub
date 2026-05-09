/* ============================================================
   SUBMIT IDEA — multi-step form + client-side validation
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const step1   = document.getElementById('step1');
  const step2   = document.getElementById('step2');
  const dot1    = document.getElementById('dot1');
  const dot2    = document.getElementById('dot2');
  const nextBtn = document.getElementById('nextStep1');
  const prevBtn = document.getElementById('prevStep2');
  const visualPanel = document.getElementById('submitVisualPanel');
  const formEl      = document.getElementById('submitIdeaForm');

  function syncSubmitVisual(step) {
    if (!visualPanel) return;
    visualPanel.dataset.activeStep = String(step);
    const numEl   = document.getElementById('visualStepNum');
    const slugEl  = document.getElementById('visualStepSlug');
    const headEl  = document.getElementById('visualHeadline');
    const blurEl  = document.getElementById('visualBlurb');
    if (!numEl || !slugEl || !headEl || !blurEl) return;

    if (step === 2) {
      numEl.textContent = '2';
      slugEl.textContent = 'Build';
      headEl.textContent = 'Tell the full story';
      blurEl.textContent =
        'Pitch the problem and solution — tags, emoji, attachments polish how it reaches collaborators.';
      return;
    }
    numEl.textContent = '1';
    slugEl.textContent = 'Spark';
    headEl.textContent = 'Name the spark';
    blurEl.textContent =
      'Title, hook, category — shape how your idea lands in the feed.';
  }

  if (!step1 || !step2) return;

  syncSubmitVisual(step1.classList.contains('active') ? 1 : step2.classList.contains('active') ? 2 : 1);

  // ── Step 1 → Step 2 ──────────────────────────────────────────
  nextBtn.addEventListener('click', () => {
    const title    = document.querySelector('[name="title"]');
    const summary  = document.querySelector('[name="summary"]');
    const category = document.querySelector('[name="category"]');
    let valid = true;

    // Title: 3–80 chars
    if (!title.value.trim() || title.value.trim().length < 3) {
      title.classList.add('is-invalid');
      valid = false;
    } else {
      title.classList.remove('is-invalid');
    }

    // Summary: 10–200 chars
    if (!summary.value.trim() || summary.value.trim().length < 10) {
      summary.classList.add('is-invalid');
      valid = false;
    } else {
      summary.classList.remove('is-invalid');
    }

    // Category: must not be empty option
    if (!category.value) {
      category.classList.add('is-invalid');
      valid = false;
    } else {
      category.classList.remove('is-invalid');
    }

    if (valid) {
      step1.classList.remove('active');
      step2.classList.add('active');
      dot1.classList.remove('active');
      dot2.classList.add('active');
      syncSubmitVisual(2);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });

  // ── Step 2 → Step 1 ──────────────────────────────────────────
  prevBtn.addEventListener('click', () => {
    step2.classList.remove('active');
    step1.classList.add('active');
    dot2.classList.remove('active');
    dot1.classList.add('active');
    syncSubmitVisual(1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // ── Step 2 validation on submit ──────────────────────────────
  if (formEl) {
    formEl.addEventListener('submit', (e) => {
      const desc = document.querySelector('[name="description"]');
      if (!desc.value.trim() || desc.value.trim().length < 20) {
        e.preventDefault();
        desc.classList.add('is-invalid');
      } else {
        desc.classList.remove('is-invalid');
      }
    });
  }

  // ── Character counter for summary ────────────────────────────
  const summary = document.querySelector('[name="summary"]');
  if (summary) {
    const counter = document.createElement('div');
    counter.className = 'form-text text-end';
    counter.textContent = `0 / 200`;
    summary.parentNode.appendChild(counter);
    summary.addEventListener('input', () => {
      const len = summary.value.length;
      counter.textContent = `${len} / 200`;
      counter.style.color = len > 200 ? 'var(--danger, red)' : '';
    });
  }

  // ── File upload UI (step 2 drop zone) ──────────────────────────────
  const dropZone    = document.getElementById('uploadDropZone');
  const fileInput   = document.getElementById('fileInput');
  const previewList = document.getElementById('filePreviewList');
  const pendingFiles = [];

  if (dropZone && fileInput) {
    ['dragenter', 'dragover'].forEach(e =>
      dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add('drag-over'); })
    );
    ['dragleave', 'drop'].forEach(e =>
      dropZone.addEventListener(e, () => dropZone.classList.remove('drag-over'))
    );
    dropZone.addEventListener('drop', ev => {
      ev.preventDefault();
      handleFiles(Array.from(ev.dataTransfer.files));
    });
    fileInput.addEventListener('change', () => {
      handleFiles(Array.from(fileInput.files));
      fileInput.value = '';
    });
  }

  function handleFiles(files) {
    const allowed = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'pptx', 'docx'];
    files.forEach(file => {
      if (pendingFiles.length >= 3) { alert('Maximum 3 files per idea.'); return; }
      const ext = file.name.split('.').pop().toLowerCase();
      if (!allowed.includes(ext)) { alert(`"${file.name}" is not an allowed file type.`); return; }
      if (file.size > 8 * 1024 * 1024) { alert(`"${file.name}" exceeds 8 MB.`); return; }
      pendingFiles.push(file);
      renderPreview(file, pendingFiles.length - 1);
    });
  }

  function renderPreview(file, index) {
    const chip = document.createElement('div');
    chip.className = 'file-preview-chip';
    chip.dataset.index = index;
    if (file.type.startsWith('image/')) {
      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      chip.appendChild(img);
    } else {
      const icon = document.createElement('i');
      icon.className = 'bi bi-file-earmark';
      chip.appendChild(icon);
    }
    const name = document.createElement('span');
    name.textContent = file.name;
    const remove = document.createElement('span');
    remove.className = 'remove-file';
    remove.innerHTML = '&times;';
    remove.addEventListener('click', () => { pendingFiles.splice(index, 1); chip.remove(); });
    chip.append(name, remove);
    previewList.appendChild(chip);
  }

  // ── Decorative panel tilt (mouse only, respects reduced-motion) ─
  const visualCard = document.querySelector('.submit-visual-card');
  const mqReduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  const figuresWrap = visualCard ? visualCard.querySelector('.submit-visual-card__figures') : null;

  if (visualCard && figuresWrap && !mqReduce.matches) {
    let raf = 0;
    visualCard.addEventListener('mousemove', (ev) => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const r = visualCard.getBoundingClientRect();
        const px = (ev.clientX - r.left) / r.width - 0.5;
        const py = (ev.clientY - r.top) / r.height - 0.5;
        figuresWrap.style.transform =
          `perspective(920px) rotateX(${(-py * 8).toFixed(2)}deg) rotateY(${(px * 10).toFixed(2)}deg)`;
      });
    });
    visualCard.addEventListener('mouseleave', () => {
      figuresWrap.style.transform = '';
    });
  }
});