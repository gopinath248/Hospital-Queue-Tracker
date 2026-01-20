// admin-dashboard.js

// Attach event listener to all forms in the table
document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll("form[action='/update_status']");

  forms.forEach(form => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault(); // prevent full page reload

      const formData = new FormData(form);

      try {
        const res = await fetch("/update_status", {
          method: "POST",
          body: formData
        });
        const data = await res.json();

        if (data.status === "success") {
          alert("Patient status updated successfully!");
        } else {
          alert("Error: " + data.error);
        }
      } catch (err) {
        console.error("Update failed:", err);
        alert("Update failed. Check console for details.");
      }
    });
  });
});