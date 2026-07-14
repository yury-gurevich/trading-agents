/* Dashboard frontend — live Sections I/II, log drawer, and status-line vitals. */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function get(path) { return fetch(path).then(function (r) { return r.json(); }); }
  function chip(status, text) {
    return "<span class='chip " + esc(status) + "'>" + esc(text) + "</span>";
  }
  function money(value, currency) {
    if (value == null) return "unavailable";
    var amount = Number(value), digits = amount > 0 && amount < 0.01 ? 4 : 2;
    var prefix = currency === "AUD" ? "A$" : currency === "USD" ? "US$" : "$";
    return prefix + amount.toFixed(digits);
  }
  function card(title, big, badge, sub) {
    return "<div class='card'><h4>" + esc(title) + "</h4><div class='statline'><span class='big'>" +
      esc(big) + "</span>" + badge + "</div><div class='sub'>" + sub + "</div></div>";
  }

  /* Transient Azure read failures self-heal: one pending refetch per section. */
  var retryTimers = {};
  var currentRun = null;
  function scheduleRetry(key, fn) {
    if (retryTimers[key]) return;
    retryTimers[key] = setTimeout(function () { delete retryTimers[key]; fn(); }, 45000);
  }

  function renderInfra(data) {
    var env = data.environment, hw = data.hardware_cost, llm = data.llm_cost;
    var services = (hw.services || []).map(function (r) {
      return esc(r.service) + " " + money(r.cost, r.currency);
    }).join(" · ") || esc(hw.message || "No billed services this month");
    var models = (llm.models || []).map(function (r) {
      return esc(r.model) + " " + (r.status === "untracked" ? "untracked" : money(r.cost, llm.currency));
    }).join(" · ") || "No ledger calls this month";
    models += "<br>CBA Send IMT · 1 USD = A$" + esc(llm.fx.aud_per_usd) + " · " + esc(llm.fx.rate_as_of);
    $("infracards").innerHTML = [
      card("Container Apps env", env.app_count == null ? "unavailable" : env.app_count + " apps",
        chip(data.available ? "good" : "idle", data.available ? "provisioned" : "unavailable"),
        esc(env.name) + (env.location ? " · " + esc(env.location) : "")),
      card("Postgres spine", data.spine.status, chip(data.spine.status === "reachable" ? "good" : "crit", data.spine.detail),
        "read-only graph projection"),
      card("Service Bus", data.bus.status, chip(data.bus.status === "reachable" ? "good" : "idle", "activation evidence"),
        esc(data.bus.detail)),
      card("Dispatcher job", data.job.status, chip(data.job.status === "Succeeded" ? "good" : "warn", data.job.name),
        "last " + esc(data.job.last_start || data.job.message || "unavailable") + " · next " + esc(data.job.next_fire)),
      card("Scale window", "scale-to-zero", chip("", "by design"),
        "master " + esc(data.scale_windows.master) + " · agents " + esc(data.scale_windows.agents)),
      card("Hardware cost · month to date", money(hw.total, hw.currency), chip(hw.available ? "good" : "warn", hw.available ? hw.currency : "unavailable"), services),
      card("LLM cost · month to date", money(llm.total, llm.currency), chip(llm.untracked_models ? "warn" : "good", llm.untracked_models + " untracked models"), models)
    ].join("");
    $("containerbody").innerHTML = data.containers.length ? data.containers.map(containerRow).join("") :
      "<tr><td colspan='6' class='muted'>Azure data unavailable — graph-backed panels remain live.</td></tr>";
    $("raildot-infra").className = "dot " + (data.available ? "good" : "idle");
    $("raillbl-infra").textContent = data.available ? env.app_count + " apps" : "couldn't verify — retrying";
    if (!data.available) scheduleRetry("infra", function () { get("/api/infra").then(renderInfra); });
  }

  function containerRow(row) {
    var replicas = row.replicas == null ? "—" : esc(row.replicas);
    var state = row.state === "healthy" || row.state === "succeeded" ? "good" : "warn";
    return "<tr><td class='mono'>" + esc(row.name) + (row.kind === "job" ? " " + chip("", "job") : "") +
      "</td><td class='mono'>:" + esc(row.image_tag) + "</td><td>" + replicas +
      "</td><td class='mono'>" + esc(row.last_window || "—") + "</td><td>" + chip(state, row.state) +
      "</td><td><button class='logbtn' data-container='" + esc(row.name) + "'>view logs</button></td></tr>";
  }

  function renderFleet(data) {
    $("fleetruntag").textContent = "Scoped to " + data.run_id;
    $("lifeflow").innerHTML = data.stages.map(function (s, i) {
      var html = "<div class='stage'><div class='node" + (s.status === "crit" ? " crit-edge" : "") + "'>" +
        "<div class='who'>" + esc(s.who) + "</div><div class='did'>" + esc(s.did) + "</div>" +
        "<div class='num'>" + esc(s.detail) + "</div><div class='verdict'>" + chip(s.status, s.verdict) + "</div></div></div>";
      setTimeout(function () { var nodes = $("lifeflow").children; if (nodes[i]) nodes[i].classList.add("revealed"); }, 110 * i + 50);
      return html;
    }).join("");
    var ladder = [];
    if (!data.escalations.length && !data.remediation_plans.length) ladder.push(chip("good", "no escalations in scope"));
    data.escalations.forEach(function (e) { ladder.push(chip(e.status === "open" ? "crit" : "good", "escalation · " + e.agent_type + " · " + e.status)); });
    data.remediation_plans.forEach(function (p) { ladder.push(chip(p.auto_eligible ? "warn" : "idle", "plan · " + p.remediation + " · " + p.status)); });
    $("fleetladder").innerHTML = ladder.join(" ");
    $("agentstates").innerHTML = data.agents.map(function (a) {
      return chip(a.escalation ? "crit" : (a.state === "active" ? "good" : "warn"), a.agent + " · " + a.state + (a.escalation ? " · " + a.escalation : ""));
    }).join(" ");
    var worst = data.stages.some(function (s) { return s.status === "crit"; }) ? "crit" :
      data.stages.some(function (s) { return s.status === "warn"; }) ? "warn" :
      data.stages.some(function (s) { return s.status === "idle"; }) ? "idle" : "good";
    $("raildot-fleet").className = "dot " + worst;
    $("raillbl-fleet").textContent = worst === "good" ? "all stages ✓" :
      worst === "idle" ? "couldn't verify — retrying" : "attention";
    if (worst === "idle") scheduleRetry("fleet", function () {
      if (data.run_id !== currentRun) return;
      get("/api/fleet?run_id=" + encodeURIComponent(data.run_id)).then(renderFleet);
    });
  }

  function renderVitals(data) {
    var sync = data.broker_graph.status, feeds = data.degraded_feeds, images = data.images, cost = data.mtd_cost;
    var flags = data.pending_flags ? vital("crit", data.pending_flags + " flag" + (data.pending_flags > 1 ? "s" : "") + " pending") : vital("good", "no pending flags");
    var syncText = sync === "in_sync" ? "broker↔graph in sync" : sync === "diverged" ? "broker↔graph DIVERGED" : "broker↔graph unavailable";
    var imageText = images.available ? "images " + images.tags.map(function (t) { return ":" + t; }).join(", ") : "images unavailable";
    var costText = cost.status === "split_currency" ? "mtd hw " + money(cost.hardware, cost.hardware_currency) + " · llm " + money(cost.llm, cost.llm_currency) :
      cost.total == null ? "mtd partial (hw unavailable · llm " + money(cost.llm, cost.llm_currency) + ")" :
        "mtd " + money(cost.total, cost.currency) + " (hw " + money(cost.hardware, cost.hardware_currency) + " · llm " + money(cost.llm, cost.llm_currency) + ")";
    $("vitals").innerHTML = [flags, vital(sync === "in_sync" ? "good" : sync === "diverged" ? "crit" : "idle", syncText),
      vital(feeds.count ? "warn" : "good", feeds.count + " feeds degraded"),
      vital(data.spine.status === "reachable" && data.bus.status === "reachable" ? "good" : "warn", "spine " + data.spine.status + " · bus " + data.bus.status),
      vital(images.available ? "good" : "idle", imageText), vital(cost.total == null ? "warn" : "good", costText),
      vital("idle", "next fire " + data.next_fire)].join("");
  }

  function vital(status, text) {
    return "<span class='vital" + (status === "crit" ? " crit" : "") + "'><span class='dot " + status + "'></span>" + esc(text) + "</span>";
  }

  function openLogs(name) {
    $("drawertitle").textContent = name;
    $("drawersub").textContent = "live Log Analytics · bounded tail";
    $("drawerbody").innerHTML = "<p class='muted'>Loading…</p>";
    $("drawer").classList.add("open"); $("drawer").setAttribute("aria-hidden", "false"); $("scrim").classList.add("on");
    var runParam = currentRun ? "&run=" + encodeURIComponent(currentRun) : "";
    get("/api/containers/" + encodeURIComponent(name) + "/logs?tail=200" + runParam).then(function (data) {
      $("drawertitle").textContent = name + (data.scope === "run" ? " — selected run window" : " — last window");
      $("drawersub").textContent = data.available ? "real data · " + data.window.start + " — " + data.window.end : data.message;
      $("drawerbody").innerHTML = data.rows.length ? data.rows.map(function (row) {
        return "<div><span class='t'>" + esc(row.timestamp) + "</span>  <span class='lv-" + esc(row.level) + "'>" + esc(row.level.toUpperCase()) + "</span>  " + esc(row.message) + "</div>";
      }).join("") : "<p class='muted'>No log rows in the bounded window.</p>";
    });
  }
  function closeLogs() { $("drawer").classList.remove("open"); $("drawer").setAttribute("aria-hidden", "true"); $("scrim").classList.remove("on"); }

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".logbtn"); if (button) openLogs(button.getAttribute("data-container"));
    if (event.target.closest("#drawer .close") || event.target === $("scrim")) closeLogs();
  });
  document.addEventListener("keydown", function (event) { if (event.key === "Escape") closeLogs(); });
  window.addEventListener("dashboard:run-selected", function (event) {
    var runId = event.detail.runId, query = "?run_id=" + encodeURIComponent(runId);
    currentRun = runId;
    get("/api/fleet" + query).then(renderFleet); get("/api/vitals" + query).then(renderVitals);
  });
  get("/api/infra").then(renderInfra);
  get("/api/vitals").then(renderVitals);
})();
