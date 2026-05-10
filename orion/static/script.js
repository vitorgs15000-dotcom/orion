const body = document.body;
const csrfToken = body.dataset.csrfToken;
const sidebar = document.querySelector("#sidebar");
const menuToggle = document.querySelector("#menu-toggle");
const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const userInput = document.querySelector("#user-id");
const messageInput = document.querySelector("#message");
const sendButton = document.querySelector("#send-button");
const sourceLabel = document.querySelector("#source-label");
const logoutButton = document.querySelector("#logout-button");
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
    if (!deferredInstallPrompt) return;
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
  const insideSidebar = sidebar.contains(event.target);
  const insideMenu = menuToggle.contains(event.target);
  if (!insideSidebar && !insideMenu) {
    sidebar.classList.remove("open");
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    const prompt = button.dataset.prompt || "";
    if (prompt) {
      messageInput.value = prompt;
      messageInput.focus();
    }
    sidebar.classList.remove("open");
  });
});

document.querySelector("[data-action='new-chat']").addEventListener("click", () => {
  messages.innerHTML = "";
  addMessage("Novo chat iniciado. Como posso te ajudar?", "assistant");
  messageInput.value = "";
  messageInput.focus();
  sidebar.classList.remove("open");
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
  article.appendChild(bubble);
  messages.appendChild(article);
  requestAnimationFrame(() => {
    messages.scrollTop = messages.scrollHeight;
  });
  return article;
}

async function sendMessage(message) {
  addMessage(message, "user", "entering");
  const thinking = addMessage("Orion pensando...", "assistant", "thinking entering");
  const thinkingBubble = thinking.querySelector(".bubble");
  sendButton.disabled = true;
  sourceLabel.textContent = "PROCESSANDO";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({
        user_id: userInput.value || "guest",
        message,
      }),
    });

    const data = await response.json();
    thinking.classList.remove("thinking");
    thinkingBubble.textContent = data.reply || data.error || "Orion nao conseguiu responder agora.";
    sourceLabel.textContent = data.source ? data.source.toUpperCase() : "ORION";
  } catch (_error) {
    thinking.classList.remove("thinking");
    thinkingBubble.textContent = "Nao consegui conectar ao servidor do Orion.";
    sourceLabel.textContent = "OFFLINE";
  } finally {
    sendButton.disabled = false;
    messageInput.focus();
    messages.scrollTop = messages.scrollHeight;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;
  messageInput.value = "";
  await sendMessage(message);
});
