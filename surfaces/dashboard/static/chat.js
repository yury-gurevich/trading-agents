/* Operator chat dock — bounded request/response turns over /api/chat. */
(function () {
  "use strict";

  var dock = document.getElementById("chat");
  var head = dock.querySelector(".chat-head");
  var body = document.getElementById("chat-body");
  var state = document.getElementById("chat-state");
  var transcript = document.getElementById("chat-transcript");
  var asks = document.getElementById("chat-asks");
  var form = document.getElementById("chat-form");
  var input = document.getElementById("chat-input");
  var working = false;

  function selectedRun() {
    return document.getElementById("run").value;
  }

  function toggle() {
    var open = body.hidden;
    body.hidden = !open;
    head.setAttribute("aria-expanded", String(open));
    if (open && !form.hidden) input.focus();
  }

  function setWorking(value) {
    working = value;
    state.textContent = value ? "Working…" : "";
    input.disabled = value;
    form.querySelector("button").disabled = value;
    asks.querySelectorAll("button").forEach(function (button) {
      button.disabled = value;
    });
  }

  function addMessage(role, text) {
    var item = document.createElement("div");
    item.className = "chat-msg " + (role === "you" ? "user" : "operator");
    var who = document.createElement("div");
    who.className = "who";
    who.textContent = role === "you" ? "Operator (you)" : "Operator agent";
    var copy = document.createElement("p");
    copy.textContent = text;
    item.appendChild(who);
    item.appendChild(copy);
    transcript.appendChild(item);
    body.scrollTop = body.scrollHeight;
    return item;
  }

  function renderTurn(turn, original, requestId) {
    var item = addMessage("operator", turn.message || "No response.");
    if (turn.outcome !== "needs_confirmation" || !turn.typed_intent) return;
    var intent = document.createElement("pre");
    intent.className = "chat-intent";
    intent.textContent = JSON.stringify(turn.typed_intent, null, 2);
    var confirm = document.createElement("button");
    confirm.className = "chat-confirm";
    confirm.type = "button";
    confirm.textContent = "Confirm";
    confirm.addEventListener("click", function () {
      confirm.disabled = true;
      send(original, true, requestId);
    });
    item.appendChild(intent);
    item.appendChild(confirm);
  }

  function send(message, confirmed, requestId) {
    if (working || !selectedRun()) return;
    addMessage("you", confirmed ? "Confirm: " + message : message);
    setWorking(true);
    fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        run_id: selectedRun(),
        confirmed: Boolean(confirmed),
        request_id: requestId || null
      })
    }).then(function (response) {
      return response.json();
    }).then(function (data) {
      if (!data.connected) {
        disconnect(data.message);
        return;
      }
      if (data.error) throw new Error(data.error);
      renderTurn(data.turn, message, data.request_id);
    }).catch(function (error) {
      addMessage("operator", "Chat could not complete this turn: " + error.message);
    }).finally(function () {
      setWorking(false);
    });
  }

  function disconnect(message) {
    document.body.classList.remove("resume-wired");
    dock.classList.remove("connected");
    state.textContent = message || "chat is not connected on this deployment";
    transcript.replaceChildren();
    asks.hidden = true;
    form.hidden = true;
  }

  head.addEventListener("click", toggle);
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var message = input.value.trim();
    if (!message) return;
    input.value = "";
    send(message, false);
  });
  asks.addEventListener("click", function (event) {
    var button = event.target.closest("button[data-ask]");
    if (button) send(button.getAttribute("data-ask"), false);
  });
  window.addEventListener("dashboard:run-selected", function () {
    transcript.replaceChildren();
  });
  window.addEventListener("dashboard:resume-request", function (event) {
    if (!dock.classList.contains("connected")) return;
    if (body.hidden) toggle();
    send("Resume from " + event.detail.stage, false);
  });

  fetch("/api/chat").then(function (response) {
    return response.json();
  }).then(function (data) {
    if (!data.connected) {
      disconnect(data.message);
      return;
    }
    dock.classList.add("connected");
    document.body.classList.add("resume-wired");
    state.textContent = "";
    asks.hidden = false;
    form.hidden = false;
  }).catch(function () {
    disconnect("chat is not connected on this deployment");
  });
})();
