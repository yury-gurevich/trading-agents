/* Dashboard status-line tile: how long the pack has run without a human.
   A window of sessions, not the selected run, so a run change never reloads it;
   a window with nothing to count shows no number. */
(function () {
  "use strict";
  var slot = document.getElementById("vital-scorecard");
  if (!slot) return;
  var counting = { tone: "idle", text: "unattended: counting" };
  var idle = { tone: "idle", text: "unattended: unavailable" };

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function rows(list) {
    return (list || []).map(function (row) {
      return "<div class='perfrow'><span>" + esc(row[0]) + "</span><b>" + esc(row[1]) + "</b></div>";
    }).join("");
  }

  function render(data) {
    if (!data || data.error || !data.text) data = idle;
    var tone = ["good", "warn", "crit", "idle"].indexOf(data.tone) >= 0 ? data.tone : "idle";
    var detail = rows(data.detail);
    var missing = (data.not_counted || []).map(function (text) {
      return "<li>" + esc(text) + "</li>";
    }).join("");
    var panel = detail ? "<div class='perfdetail cardetail' hidden>" + detail +
      "<h4>Sessions, newest first</h4>" + rows(data.sessions) +
      "<h4>Not counted: the graph does not record</h4><ul>" + missing + "</ul>" +
      "<p>" + esc(data.summary) + "</p></div>" : "";
    var title = detail ? "Show the sessions" : (data.reason || data.text);
    slot.innerHTML = "<button type='button' class='vital perfvital" + (tone === "crit" ? " crit" : "") +
      "' title='" + esc(title) + "' aria-expanded='false'" + (detail ? "" : " disabled") + ">" +
      "<span class='dot " + tone + "'></span>" + esc(data.text) + "</button>" + panel;
  }

  function load() {
    fetch("/api/scorecard")
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
  window.addEventListener("dashboard:command-completed", load);
  render(counting);
  load();
})();
