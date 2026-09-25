/* Dashboard status-line vital: the book against the market, for the selected run.
   Prints the reporter's stored numbers; a run without a scoreboard shows no number. */
(function () {
  "use strict";
  var slot = document.getElementById("vital-performance");
  if (!slot) return;
  var currentRun = "";
  var idle = { tone: "idle", text: "no scoreboard for this run" };

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function render(data) {
    if (!data || data.error || !data.text) data = idle;
    var tone = ["good", "warn", "crit", "idle"].indexOf(data.tone) >= 0 ? data.tone : "idle";
    var rows = (data.detail || []).map(function (row) {
      return "<div class='perfrow'><span>" + esc(row[0]) + "</span><b>" + esc(row[1]) + "</b></div>";
    }).join("");
    var panel = rows ? "<div class='perfdetail' hidden>" + rows + "<p>" + esc(data.summary) + "</p></div>" : "";
    var title = rows ? "Show the numbers" : (data.reason || data.text);
    slot.innerHTML = "<button type='button' class='vital perfvital" + (tone === "crit" ? " crit" : "") +
      "' title='" + esc(title) + "' aria-expanded='false'" + (rows ? "" : " disabled") + ">" +
      "<span class='dot " + tone + "'></span>" + esc(data.text) + "</button>" + panel;
  }

  function load(runId) {
    currentRun = runId || currentRun;
    if (!currentRun) { render(idle); return; }
    fetch("/api/runs/" + encodeURIComponent(currentRun) + "/performance")
      .then(function (r) { return r.json(); })
      .then(render)
      .catch(function () { render(idle); });
  }

  slot.addEventListener("click", function (event) {
    var button = event.target.closest(".perfvital");
    var panel = slot.querySelector(".perfdetail");
    if (!button || !panel) return;
    panel.hidden = !panel.hidden;
    button.setAttribute("aria-expanded", String(!panel.hidden));
  });
  document.addEventListener("keydown", function (event) {
    var panel = slot.querySelector(".perfdetail");
    if (event.key === "Escape" && panel) panel.hidden = true;
  });
  window.addEventListener("dashboard:run-selected", function (event) { load(event.detail.runId); });
  window.addEventListener("dashboard:command-completed", function () { load(currentRun); });
  render(idle);
})();
