// Basic client-side registration flow for static demo.
(function registerPageSetup() {
  const form = document.getElementById("registerForm");
  if (!form) {
    console.log("Idea Incubator skeleton loaded.");
    return;
  }

  const alertBox = document.getElementById("registerAlert");
  const storageKey = "ideaIncubatorUsers";

  function showAlert(type, message) {
    if (!alertBox) {
      return;
    }
    alertBox.className = `alert alert-${type}`;
    alertBox.textContent = message;
  }

  form.addEventListener("submit", function onSubmit(event) {
    event.preventDefault();

    const name = String(document.getElementById("name")?.value || "").trim();
    const email = String(document.getElementById("email")?.value || "").trim().toLowerCase();
    const password = String(document.getElementById("password")?.value || "");
    const confirmPassword = String(document.getElementById("confirmPassword")?.value || "");

    if (name.length < 2) {
      showAlert("danger", "Name must be at least 2 characters.");
      return;
    }
    if (!email || !email.includes("@")) {
      showAlert("danger", "Please enter a valid email address.");
      return;
    }
    if (password.length < 6) {
      showAlert("danger", "Password must be at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      showAlert("danger", "Passwords do not match.");
      return;
    }

    let users = [];
    try {
      users = JSON.parse(localStorage.getItem(storageKey) || "[]");
      if (!Array.isArray(users)) {
        users = [];
      }
    } catch (error) {
      users = [];
    }

    const exists = users.some(function hasSameEmail(user) {
      return String(user.email || "").toLowerCase() === email;
    });

    if (exists) {
      showAlert("danger", "This email is already registered.");
      return;
    }

    users.push({
      name: name,
      email: email,
      password: password,
      createdAt: new Date().toISOString()
    });
    localStorage.setItem(storageKey, JSON.stringify(users));

    showAlert("success", "Registration successful! Redirecting to home page...");
    form.reset();
    window.setTimeout(function redirectToHome() {
      window.location.href = "index.html";
    }, 1200);
  });
})();
