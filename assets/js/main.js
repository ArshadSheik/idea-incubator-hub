// Basic client-side behavior for static pages.
(function setupEditIdeaPage() {
  const form = document.getElementById("editIdeaForm");
  if (!form) {
    console.log("Idea Incubator skeleton loaded.");
    return;
  }

  const alertBox = document.getElementById("editIdeaAlert");
  const storageKey = "ideaIncubatorDraftIdea";

  function showAlert(type, message) {
    if (!alertBox) {
      return;
    }
    alertBox.className = `alert alert-${type}`;
    alertBox.textContent = message;
  }

  function setValue(id, value) {
    const input = document.getElementById(id);
    if (input) {
      input.value = value || "";
    }
  }

  function getValue(id) {
    const input = document.getElementById(id);
    return String(input?.value || "").trim();
  }

  try {
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      const draft = JSON.parse(raw);
      setValue("ideaTitle", draft.title);
      setValue("ideaTag", draft.tag);
      setValue("ideaStage", draft.stage);
      setValue("ideaSummary", draft.summary);
      setValue("ideaDescription", draft.description);
    }
  } catch (error) {
    // Ignore invalid localStorage data and continue with empty form.
  }

  form.addEventListener("submit", function onSubmit(event) {
    event.preventDefault();

    const draftIdea = {
      title: getValue("ideaTitle"),
      tag: getValue("ideaTag"),
      stage: getValue("ideaStage"),
      summary: getValue("ideaSummary"),
      description: getValue("ideaDescription"),
      updatedAt: new Date().toISOString()
    };

    if (draftIdea.title.length < 5) {
      showAlert("danger", "Idea title must be at least 5 characters.");
      return;
    }
    if (!draftIdea.tag) {
      showAlert("danger", "Please select a category.");
      return;
    }
    if (!draftIdea.stage) {
      showAlert("danger", "Please select the current stage.");
      return;
    }
    if (draftIdea.summary.length < 10) {
      showAlert("danger", "Summary must be at least 10 characters.");
      return;
    }
    if (draftIdea.description.length < 30) {
      showAlert("danger", "Detailed description must be at least 30 characters.");
      return;
    }

    localStorage.setItem(storageKey, JSON.stringify(draftIdea));
    showAlert("success", "Idea updated successfully.");
  });
})();
