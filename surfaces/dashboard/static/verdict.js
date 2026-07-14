/* Master-verdict hero — follows the selected run and renders server wording. */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };

  function render(data) {
    var hero = $("verdict-hero");
    var light = data.light === "GREEN" ? "green" : "red";
    hero.dataset.light = light;
    hero.setAttribute("aria-label", data.light + ". " + data.summary);
    $("master-light-label").textContent = data.light;
    $("verdict-summary").textContent = data.summary;
    var day = String(data.run_id || "").match(/\d{4}-\d{2}-\d{2}/);
    $("verdict-run-day").textContent = day ? day[0] : (data.run_id || "—");
    $("verdict-next-fire").textContent = data.next_fire || "unavailable";

    var warnings = data.warnings || [];
    var detail = $("warning-detail");
    detail.classList.toggle("no-warnings", warnings.length === 0);
    detail.open = false;
    $("warning-badge").textContent = warnings.length +
      (warnings.length === 1 ? " warning" : " warnings");
    var rows = $("warning-rows");
    rows.replaceChildren();
    warnings.forEach(function (warning) {
      var item = document.createElement("li");
      item.textContent = warning.message;
      rows.appendChild(item);
    });
  }

  function unavailable() {
    render({
      light: "RED",
      summary: "The run verdict is unavailable.",
      next_fire: "unavailable",
      warnings: []
    });
  }

  window.addEventListener("dashboard:run-selected", function (event) {
    var runId = event.detail.runId;
    fetch("/api/verdict?run=" + encodeURIComponent(runId))
      .then(function (response) {
        if (!response.ok) throw new Error("verdict unavailable");
        return response.json();
      })
      .then(render)
      .catch(unavailable);
  });
})();
