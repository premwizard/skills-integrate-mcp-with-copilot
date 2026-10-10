document.addEventListener("DOMContentLoaded", () => {
  const activitiesTableWrapper = document.getElementById("activities-table-wrapper");
  const form = document.getElementById("new-activity-form");
  const messageDiv = document.getElementById("message");

  async function showMessage(text, type = "success") {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();
      renderActivities(activities);
    } catch (error) {
      console.error("Error fetching activities:", error);
      showMessage("Failed to load activities.", "error");
    }
  }

  function renderActivities(activities) {
    const html = Object.entries(activities)
      .map(([name, details]) => {
        return `
          <div class="activity-card">
            <h4>${name}</h4>
            <p>${details.description}</p>
            <p><strong>Schedule:</strong> ${details.schedule}</p>
            <p><strong>Max participants:</strong> ${details.max_participants}</p>
            <p><strong>Signed up:</strong> ${details.participants.length}</p>
            <button class="delete-activity" data-activity="${encodeURIComponent(name)}">Delete Activity</button>
          </div>
        `;
      })
      .join("");

    activitiesTableWrapper.innerHTML = html || "<p>No activities found.</p>";

    document.querySelectorAll(".delete-activity").forEach((button) => {
      button.addEventListener("click", handleDeleteActivity);
    });
  }

  async function handleDeleteActivity(event) {
    const name = decodeURIComponent(event.target.dataset.activity);
    try {
      const response = await fetch(`/admin/activities/${encodeURIComponent(name)}`, { method: "DELETE" });
      const result = await response.json();
      if (response.ok) {
        showMessage(result.message, "success");
        fetchActivities();
      } else {
        showMessage(result.detail || "Failed to delete activity.", "error");
      }
    } catch (error) {
      console.error("Error deleting activity:", error);
      showMessage("Failed to delete activity.", "error");
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = document.getElementById("name").value.trim();
    const description = document.getElementById("description").value.trim();
    const schedule = document.getElementById("schedule").value.trim();
    const maxParticipants = Number(document.getElementById("max_participants").value);

    try {
      const response = await fetch("/admin/activities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description, schedule, max_participants: maxParticipants }),
      });
      const result = await response.json();
      if (response.ok) {
        showMessage(result.message, "success");
        form.reset();
        fetchActivities();
      } else {
        showMessage(result.detail || "Failed to create activity.", "error");
      }
    } catch (error) {
      console.error("Error creating activity:", error);
      showMessage("Failed to create activity.", "error");
    }
  });

  fetchActivities();
});
