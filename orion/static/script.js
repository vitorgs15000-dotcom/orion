const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const userInput = document.querySelector("#user-id");
const messageInput = document.querySelector("#message");
const sendButton = document.querySelector("#send-button");
const sourceLabel = document.querySelector("#source-label");
const sidebar = document.querySelector("#sidebar");
const menuToggle = document.querySelector("#menu-toggle");
const logoutButton = document.querySelector("#logout-button");
const csrfToken = document.body.dataset.csrfToken;
const installButtons = [
  document.querySelector("#install-button"),
  document.querySelector("#install-button-mobile"),
].filter(Boolean);

let deferredInstallPrompt = null;

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
  });
}

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  installButtons.forEach((button) => {
    button.hidden = false;
  });
});

window.addEventListener("appinstalled", () => {
  deferredInstallPrompt = null;
  installButtons.forEach((button) => {
    button.hidden = true;
  });
});

installButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    if (!deferredInstallPrompt) {
      return;
    }

    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    installButtons.forEach((item) => {
      item.hidden = true;
    });
  });
});

menuToggle.addEventListener("click", () => {
  sidebar.classList.toggle("open");
});

document.addEventListener("click", (event) => {
  if (!sidebar.contains(event.target) && !menuToggle.contains(event.target)) {
    sidebar.classList.remove("open");
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.prompt;
    messageInput.focus();
    sidebar.classList.remove("open");
  });
});

if (logoutButton) {
  logoutButton.addEventListener("click", async () => {
    await fetch("/logout", {
      method: "POST",
      headers: { "X-CSRF-Token": csrfToken },
    });
    window.location.reload();
  });
}

function addMessage(text, type, extraClass = "") {
  const article = document.createElement("article");
  const bubble = document.createElement("div");

  article.className = `message ${type} ${extraClass}`.trim();
  bubble.className = "bubble";
  bubble.textContent = text;

  if (type === "assistant") {
    const mark = document.createElement("div");
    const logo = document.createElement("div");
    mark.className = "message-mark";
    logo.className = "mini-logo";
    mark.appendChild(logo);
    article.appendChild(mark);
  }

  article.appendChild(bubble);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

async function sendMessage(message) {
  addMessage(message, "user", "fade-in");
  const thinking = addMessage("Orion pensando...", "assistant", "thinking fade-in");
  const thinkingBubble = thinking.querySelector(".bubble");

  sourceLabel.textContent = "PROCESSANDO";
  sendButton.disabled = true;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({
        user_id: userInput.value || "default",
        message,
      }),
    });

    const data = await response.json();
    thinking.classList.remove("thinking");
    thinkingBubble.textContent = data.reply || data.error || "Orion nao conseguiu responder agora.";
    sourceLabel.textContent = data.source ? data.source.toUpperCase() : "ORION IA";
  } catch (_error) {
    thinking.classList.remove("thinking");
    thinkingBubble.textContent = "Nao consegui conectar ao servidor do Orion.";
    sourceLabel.textContent = "OFFLINE";
  } finally {
    sendButton.disabled = false;
    messageInput.focus();
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();

  if (!message) {
    return;
  }

  messageInput.value = "";
  await sendMessage(message);
});
