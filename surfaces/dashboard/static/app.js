/* Dashboard frontend — selected-run trading detail over the read-model API. */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function get(path) { return fetch(path).then(function (r) { return r.json(); }); }
  function chip(cls, text) { return "<span class='chip " + cls + "'>" + esc(text) + "</span>"; }

  var STAGE_LABEL = { pm: "portfolio mgr" };

  function renderStages(stages) {
    var host = $("tradeflow");
    var resumable = stages.some(function (stage) { return stage.reached; });
    host.innerHTML = "";
    stages.forEach(function (s, i) {
      var checks = (s.checks || []).map(function (c) {
        if (c.ok) return chip("good", "✓ " + c.key);
        return chip(c.severity === "warn" ? "warn" : "crit",
          (c.severity === "warn" ? "⚠ " : "✕ ") + c.key + ": " + c.detail);
      }).join("");
      var nums = Object.keys(s.observed || {}).map(function (k) {
        return esc(k) + "=" + esc(s.observed[k]);
      }).join(" · ");
      var failed = (s.checks || []).some(function (c) { return !c.ok && c.severity === "fail"; });
      var node = document.createElement("div");
      node.className = "stage";
      node.innerHTML = "<div class='node" + ((!s.reached || failed) ? " crit-edge" : "") + "'>" +
        "<div class='who'>" + esc(STAGE_LABEL[s.name] || s.name) + "</div>" +
        "<div class='num'>" + (s.reached ? nums || "—" : "NOT REACHED") + "</div>" +
        "<div class='verdict'>" + (s.reached ? checks || chip("good", "✓ reached") : chip("crit", "✕ not reached")) + "</div>" +
        (resumable ? "<button class='resume-action' type='button' data-resume-stage='" +
          esc(s.name) + "'>Resume from " + esc(STAGE_LABEL[s.name] || s.name) + "</button>" : "") +
        "</div>";
      node.title = (s.outputs || []).join("\n");
      host.appendChild(node);
      setTimeout(function () { node.classList.add("revealed"); }, 110 * i + 50);
    });
  }

  function renderVerdict(v) {
    var verdict = v.verdict || (v.passed ? "PASS" : "FAIL");
    var noTrade = verdict === "NO_TRADE";
    var pill = $("verdictpill");
    pill.hidden = false;
    pill.className = "pill " + (v.passed ? "pass" : "fail");
    pill.textContent = noTrade ? "✓ COMPLETED · NO TRADES" :
      (v.passed ? "✓ RUN PASSED" : "✕ RUN FAILED");
    var dot = $("raildot-trading"), lbl = $("raillbl-trading");
    dot.className = "dot " + (v.passed ? "good" : "crit");
    lbl.textContent = noTrade ? "completed · no trades" : (v.passed ? "run passed" : "run failed");

    var fails = v.breaches.filter(function (b) { return b.severity === "fail"; });
    var warns = v.breaches.filter(function (b) { return b.severity !== "fail"; });
    var html;
    if (noTrade) {
      html = "<div class='gatecard pass'><h3>Run result: completed — no trades</h3>" +
        "<p>" + esc(v.annotation) + "</p></div>";
    } else if (v.passed) {
      html = "<div class='gatecard pass'><h3>Run result: passed</h3>" +
        "<p>Every stage did its job within its boundaries.</p>" +
        (warns.length ? "<p class='mono'>" + warns.map(function (b) { return "WARN  " + esc(b.stage + "." + b.key + ": " + b.detail); }).join("<br>") + "</p>" : "") + "</div>";
    } else {
      html = "<div class='gatecard fail'><h3>Run result: failed</h3>" +
        "<p class='mono'>" + v.breaches.map(function (b) { return esc(b.severity.toUpperCase() + "  " + b.stage + "." + b.key + ": " + b.detail); }).join("<br>") + "</p></div>";
    }
    $("gate").innerHTML = html;
  }

  function renderFlags(flags) {
    if (!flags.length) { $("flagbody").innerHTML = "<p class='muted'>No flags in this run's scope.</p>"; return; }
    $("flagbody").innerHTML = flags.map(function (f) {
      return chip(f.severity === "critical" ? "crit" : "warn", "⚑ " + f.severity + " · " + f.status) +
        "<div class='flagreason'>" + esc(f.reason || f.subject_ref) + "</div>";
    }).join("");
  }

  function renderPositions(p) {
    if (!p.rows.length) { $("posbody").innerHTML = "<p class='muted'>No open positions and no broker snapshot.</p>"; return; }
    var rows = p.rows.map(function (r) {
      return "<tr><td class='mono'>" + esc(r.ticker) + "</td><td class='mono'>" + esc(r.graph_qty == null ? "—" : r.graph_qty) +
        "</td><td class='mono'>" + esc(r.broker_qty == null ? "—" : r.broker_qty) + "</td><td>" +
        (r.match ? chip("good", "✓") : chip("crit", "✕ diverged")) + "</td></tr>";
    }).join("");
    $("posbody").innerHTML = "<div style='overflow-x:auto'><table><thead><tr><th>Ticker</th><th>Graph</th><th>Broker</th><th></th></tr></thead><tbody>" +
      rows + "</tbody></table></div>" +
      (p.snapshot_at ? "<p class='muted'>snapshot " + esc(p.snapshot_at) + "</p>" : "<p class='muted'>no broker snapshot on record</p>");
  }

  function renderRecovery(r) {
    var bits = [];
    if (!r.escalations.length && !r.remediation_plans.length) {
      bits.push(chip("good", "✓ no escalations in scope"));
    }
    r.escalations.forEach(function (e) {
      bits.push(chip(e.status === "open" ? "crit" : "good",
        "escalation · " + e.agent_type + " · " + e.status + " · attempts " + e.auto_attempts));
    });
    r.remediation_plans.forEach(function (p) {
      bits.push(chip(p.auto_eligible ? "warn" : "idle", "plan · " + p.remediation + " · " + p.status));
    });
    $("recbody").innerHTML = bits.join(" ") +
      "<p class='muted' style='margin-top:8px'>Ladder: test → one automatic shot → operator.</p>";
  }

  function loadRun(runId, detailed) {
    $("runtag").textContent = "Scoped to " + runId;
    window.dispatchEvent(new CustomEvent("dashboard:run-selected", { detail: { runId: runId } }));
    if (!detailed) {
      $("runtag").textContent = "No persisted stages for " + runId;
      return;
    }
    get("/api/runs/" + runId + "/stages").then(renderStages);
    get("/api/runs/" + runId + "/verdict").then(renderVerdict);
    get("/api/runs/" + runId + "/flags").then(renderFlags);
    get("/api/runs/" + runId + "/positions").then(renderPositions);
    get("/api/runs/" + runId + "/recovery").then(renderRecovery);
  }

  document.querySelectorAll(".railbtn").forEach(function (b) {
    b.addEventListener("click", function () {
      var v = b.getAttribute("data-view");
      ["infra", "fleet", "trading"].forEach(function (id) {
        $(id).classList.toggle("active", id === v);
        document.querySelector(".railbtn[data-view='" + id + "']")
          .setAttribute("aria-current", id === v ? "true" : "false");
      });
    });
  });

  $("tradeflow").addEventListener("click", function (event) {
    var button = event.target.closest("button[data-resume-stage]");
    if (!button) return;
    window.dispatchEvent(new CustomEvent("dashboard:resume-request", {
      detail: { stage: button.getAttribute("data-resume-stage") }
    }));
  });

  get("/api/runs").then(function (runs) {
    var sel = $("run");
    sel.innerHTML = runs.map(function (r) {
      return "<option value='" + esc(r.run_id) + "'>" + esc(r.run_id) + "</option>";
    }).join("");
    var requested = new URLSearchParams(window.location.search).get("run");
    if (requested && !runs.some(function (r) { return r.run_id === requested; })) {
      sel.insertAdjacentHTML("beforeend", "<option value='" + esc(requested) + "'>" +
        esc(requested) + "</option>");
    }
    if (requested) sel.value = requested;
    function knownRun() {
      return runs.some(function (r) { return r.run_id === sel.value; });
    }
    sel.addEventListener("change", function () { loadRun(sel.value, knownRun()); });
    if (sel.value) loadRun(sel.value, knownRun());
    else $("runtag").textContent = "No runs on the graph yet.";
  });
})();
