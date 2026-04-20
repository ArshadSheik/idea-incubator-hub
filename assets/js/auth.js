/* ═══════════════════════════════════════════════
   AUTH JS — login + register
   ═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ─── Password visibility toggle ─── */
  document.querySelectorAll('[data-toggle-password]').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.togglePassword;
      const input = document.getElementById(targetId);
      const icon = btn.querySelector('i');
      if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
      } else {
        input.type = 'password';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
      }
    });
  });

  /* ─── Password strength meter (register only) ─── */
  const pwInput = document.getElementById('password');
  const strengthFill = document.getElementById('strengthFill');
  const strengthLabel = document.getElementById('strengthLabel');
  if (pwInput && strengthFill) {
    pwInput.addEventListener('input', () => {
      const score = getPasswordStrength(pwInput.value);
      strengthFill.className = 'strength-fill';
      if (pwInput.value.length === 0) {
        strengthLabel.textContent = 'Enter a password';
        return;
      }
      if (score <= 1) { strengthFill.classList.add('weak'); strengthLabel.textContent = 'Weak'; }
      else if (score === 2) { strengthFill.classList.add('fair'); strengthLabel.textContent = 'Fair'; }
      else if (score === 3) { strengthFill.classList.add('good'); strengthLabel.textContent = 'Good'; }
      else { strengthFill.classList.add('strong'); strengthLabel.textContent = 'Strong'; }
    });
  }

  function getPasswordStrength(pw) {
    let s = 0;
    if (pw.length >= 8) s++;
    if (pw.length >= 12) s++;
    if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
    if (/\d/.test(pw)) s++;
    if (/[^A-Za-z0-9]/.test(pw)) s++;
    return Math.min(s, 4);
  }

  /* ─── Generic form validation + field error display ─── */
  function showFieldError(field, show) {
    field.classList.toggle('is-invalid', show);
    const errorEl = document.querySelector(`[data-error-for="${field.id}"]`);
    if (errorEl) errorEl.classList.toggle('show', show);
  }

  function clearErrorOnInput(field) {
    field.addEventListener('input', () => {
      if (field.classList.contains('is-invalid')) showFieldError(field, false);
    });
    field.addEventListener('change', () => {
      if (field.classList.contains('is-invalid')) showFieldError(field, false);
    });
  }

  /* ─── LOGIN form ─── */
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    const email = document.getElementById('email');
    const password = document.getElementById('password');
    [email, password].forEach(clearErrorOnInput);

    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      let ok = true;

      if (!email.value || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
        showFieldError(email, true); ok = false;
      }
      if (!password.value) { showFieldError(password, true); ok = false; }

      if (ok) {
        // Frontend demo: show success-ish toast then redirect
        const alertBox = document.getElementById('loginAlert');
        alertBox.className = 'alert-iih alert-success-iih';
        alertBox.innerHTML = '<i class="bi bi-check-circle-fill"></i> <span>Welcome back! Redirecting to your dashboard…</span>';
        alertBox.style.display = 'flex';
        setTimeout(() => { window.location.href = 'dashboard.html'; }, 900);
      }
    });
  }

  /* ─── REGISTER form ─── */
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    const fields = {
      firstName: document.getElementById('firstName'),
      lastName: document.getElementById('lastName'),
      username: document.getElementById('username'),
      email: document.getElementById('email'),
      password: document.getElementById('password'),
      confirmPassword: document.getElementById('confirmPassword'),
      terms: document.getElementById('terms'),
    };
    Object.values(fields).forEach(f => { if (f.type !== 'checkbox') clearErrorOnInput(f); });

    fields.terms.addEventListener('change', () => {
      if (fields.terms.checked) {
        const err = document.querySelector(`[data-error-for="terms"]`);
        if (err) err.classList.remove('show');
      }
    });

    registerForm.addEventListener('submit', (e) => {
      e.preventDefault();
      let ok = true;

      if (!fields.firstName.value || fields.firstName.value.length < 2) { showFieldError(fields.firstName, true); ok = false; }
      if (!fields.lastName.value || fields.lastName.value.length < 2) { showFieldError(fields.lastName, true); ok = false; }
      if (!/^[a-zA-Z0-9_]{3,20}$/.test(fields.username.value)) { showFieldError(fields.username, true); ok = false; }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email.value)) { showFieldError(fields.email, true); ok = false; }
      if (fields.password.value.length < 8) { showFieldError(fields.password, true); ok = false; }
      if (fields.password.value !== fields.confirmPassword.value || !fields.confirmPassword.value) {
        showFieldError(fields.confirmPassword, true); ok = false;
      }
      if (!fields.terms.checked) {
        const err = document.querySelector(`[data-error-for="terms"]`);
        if (err) err.classList.add('show');
        ok = false;
      }

      if (ok) {
        const alertBox = document.getElementById('registerAlert');
        alertBox.className = 'alert-iih alert-success-iih';
        alertBox.innerHTML = '<i class="bi bi-check-circle-fill"></i> <span>Account created! Redirecting to your dashboard…</span>';
        alertBox.style.display = 'flex';
        setTimeout(() => { window.location.href = 'dashboard.html'; }, 1000);
      }
    });
  }
});
