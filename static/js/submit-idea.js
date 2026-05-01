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

  if (!step1 || !step2) return;

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
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });

  // ── Step 2 → Step 1 ──────────────────────────────────────────
  prevBtn.addEventListener('click', () => {
    step2.classList.remove('active');
    step1.classList.add('active');
    dot2.classList.remove('active');
    dot1.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // ── Step 2 validation on submit ──────────────────────────────
  document.getElementById('submitIdeaForm').addEventListener('submit', (e) => {
    const desc = document.querySelector('[name="description"]');
    if (!desc.value.trim() || desc.value.trim().length < 20) {
      e.preventDefault();
      desc.classList.add('is-invalid');
    } else {
      desc.classList.remove('is-invalid');
    }
  });

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
});