/* Trading panel: the book on the selected run's session, as its held forecasts read it.
   The brief's own book lines head the panel; each held name follows, the likeliest to
   reach its stop first leading. A run with no book or no forecast says so. */
(function () {
  "use strict";
  var body = document.getElementById("bookbody");
  if (!body) return;

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function money(cents) {
    if (cents == null) return "—";
    var sign = cents < 0 ? "−" : "";
    var abs = Math.abs(cents);
    var whole = Math.floor(abs / 100).toLocaleString("en-US");
    return sign + "$" + whole + "." + String(abs % 100).padStart(2, "0");
  }

  function pct(p) {
    return p == null ? "—" : Math.round(p * 100) + " %";
  }

  function row(r) {
    var past = r.past_target ? " <span class='chip good'>past target</span>" : "";
    var none = r.forecast ? "" : " <span class='chip warn'>no forecast</span>";
    return "<tr><td class='mono'>" + esc(r.ticker) + past + none + "</td><td class='mono'>" +
      esc(r.quantity) + "</td><td class='mono'>" + money(r.close_cents) + "</td><td class='mono'>" +
      money(r.stop_cents) + "</td><td class='mono'>" + money(r.target_cents) + "</td><td class='mono'>" +
      pct(r.p_target_first) + "</td><td class='mono'>" + pct(r.p_stop_first) + "</td><td class='mono'>" +
      money(r.gain_cents) + "</td></tr>";
  }

  function render(data) {
    if (!data || data.error) {
      body.innerHTML = "<p class='muted'>Book unavailable for this run.</p>";
      return;
    }
    if (!data.rows || !data.rows.length) {
      body.innerHTML = "<p class='muted'>Nothing held on this run's session.</p>";
      return;
    }
    var lines = (data.lines || []).map(function (line) {
      return "<p>" + esc(line) + "</p>";
    }).join("");
    body.innerHTML = lines + "<div style='overflow-x:auto'><table><thead><tr><th>Ticker</th>" +
      "<th>Qty</th><th>Close</th><th>Stop</th><th>Target</th><th>Target first</th>" +
      "<th>Stop first</th><th>Gain</th></tr></thead><tbody>" + data.rows.map(row).join("") +
      "</tbody></table></div><p class='muted'>Odds over the next sessions from the nightly " +
      "forecast, not yet scored on held names. Session " + esc(data.as_of) + ".</p>";
  }

  window.addEventListener("dashboard:run-selected", function (event) {
    var runId = event.detail && event.detail.runId;
    if (!runId) return;
    fetch("/api/runs/" + encodeURIComponent(runId) + "/book")
      .then(function (r) { return r.json(); })
      .then(render)
      .catch(function () { render(null); });
  });
})();
