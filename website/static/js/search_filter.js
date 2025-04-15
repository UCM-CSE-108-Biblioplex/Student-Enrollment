document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("search-form");
  const inputs = document.querySelectorAll(".form-input");

  inputs.forEach(input => {
    input.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        form.dispatchEvent(new Event("submit", { bubbles: true }));
      }
    });
  });
});
