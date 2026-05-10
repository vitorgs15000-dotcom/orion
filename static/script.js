const state = {
  currentView: "chat",
  tasks: loadTasks(),
  animations: localStorage.getItem("orion-animations") !== "off",
  deferredInstallPrompt: null,
};

const csrfToken = document.body.dataset.csrfToken;
const defaultUserId = document.body.dataset.userId || "guest";
const sidebar = document.querySelector("#sidebar");
const menuToggle = document.querySelector("#menu-toggle");
const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const userInput = document.querySelector("#user-id");
const messageInput = document.querySelector("#message");
const sendButton = document.querySelector("#send-button");
const sourceLabel = document.querySelector("#source-label");
const spaPanel = document.querySelector("#spa-panel");
const chatCard = document.querySelector("#chat-card");
const quickGrid = document.querySelector("#quick-grid");
const viewKicker = document.querySelector("#view-kicker");
const viewTitle = document.querySelector("#view-title");
const viewSubtitle = document.querySelector("#view-subtitle");
const logoutButton = document.querySelector("#logout-button");
const installButtons = [
  document.querySelector("#install-button"),
  document.querySelector("#install-button-mobile"),
].filter(Boolean);

if (!state.animations) {
  document.body.classList.add("no-animations");
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
  });
}

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  state.deferredInstallPrompt = event;
  installButtons.forEach((button) => {
    button.hidden = false;
  });
});

window.addEventListener("appinstalled", () => {
  state.deferredInstallPrompt = null;
  installButtons.forEach((button) => {
    button.hidden = true;
  });
});

installButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    if (!state.deferredInstallPrompt) return;
    state.deferredInstallPrompt.prompt();
    await state.deferredInstallPrompt.userChoice;
    state.deferredInstallPrompt = null;
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

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => setView(button.dataset.view));
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    setView("chat");
    messageInput.value = button.dataset.prompt || "";
    messageInput.focus();
  });
});

document.querySelector("#new-chat").addEventListener("click", () => {
  setView("chat");
  messages.innerHTML = "";
  addMessage("Novo chat iniciado. Processando nova linha de pensamento.", "assistant");
  sourceLabel.textContent = "ORION IA";
});

if (logoutButton) {
  logoutButton.addEventListener("click", async () => {
    await api("/logout", { method: "POST" });
    window.location.reload();
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;
  messageInput.value = "";
  await sendMessage(message);
});

function setView(view) {
  state.currentView = view === "conversations" ? "conversations" : view;
  sidebar.classList.remove("open");
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });

  if (view === "chat") {
    renderChatView();
  } else if (view === "conversations") {
    renderConversationsView();
  } else if (view === "memory") {
    renderMemoryView();
  } else if (view === "tasks") {
    renderTasksView();
  } else if (view === "settings") {
    renderSettingsView();
  }
}

function showPanel(title, subtitle, kicker = "ORION V1.1") {
  viewKicker.textContent = kicker;
  viewTitle.textContent = title;
  viewSubtitle.textContent = subtitle;
  quickGrid.hidden = true;
  chatCard.hidden = true;
  spaPanel.hidden = false;
  spaPanel.classList.add("entering");
  setTimeout(() => spaPanel.classList.remove("entering"), 180);
}

function renderChatView() {
  viewKicker.textContent = "ORION V1.1 ONLINE";
  viewTitle.textContent = "Olá, eu sou o Orion.";
  viewSubtitle.textContent = "Como posso te ajudar hoje?";
  quickGrid.hidden = false;
  spaPanel.hidden = true;
  chatCard.hidden = false;
  messageInput.focus();
}

async function renderConversationsView() {
  showPanel("Conversas", "Histórico recente do núcleo conversacional.");
  const data = await loadMemory();
  const history = data.history || [];
  spaPanel.innerHTML = `
    <div class="panel-head">
      <strong>${history.length} registros</strong>
      <button class="ghost-button" data-clear-history>Limpar histórico</button>
    </div>
    <div class="list">${history.length ? history.map(renderHistoryItem).join("") : emptyState("Nenhuma conversa registrada ainda.")}</div>
  `;
  spaPanel.querySelector("[data-clear-history]")?.addEventListener("click", clearHistory);
}

async function renderMemoryView() {
  showPanel("Memória", "Informações salvas para manter continuidade.");
  const data = await loadMemory();
  const profile = data.profile || {};
  const entries = Object.entries(profile);
  spaPanel.innerHTML = `
    <form class="inline-form" id="memory-form">
      <input name="key" placeholder="chave, exemplo: foco" maxlength="48" required />
      <input name="value" placeholder="valor, exemplo: criar o Orion" maxlength="300" required />
      <button type="submit">Salvar</button>
    </form>
    <div class="list">${entries.length ? entries.map(renderMemoryItem).join("") : emptyState("Nenhuma memória salva.")}</div>
  `;
  spaPanel.querySelector("#memory-form").addEventListener("submit", saveMemoryFact);
  spaPanel.querySelectorAll("[data-forget]").forEach((button) => {
    button.addEventListener("click", () => forgetMemoryFact(button.dataset.forget));
  });
}

function renderTasksView() {
  showPanel("Tarefas", "Organize execução sem sair do Orion.");
  spaPanel.innerHTML = `
    <form class="inline-form" id="task-form">
      <input name="task" placeholder="Nova tarefa..." maxlength="160" required />
      <button type="submit">Criar</button>
    </form>
    <div class="list">${state.tasks.length ? state.tasks.map(renderTaskItem).join("") : emptyState("Nenhuma tarefa criada.")}</div>
  `;
  spaPanel.querySelector("#task-form").addEventListener("submit", createTask);
  spaPanel.querySelectorAll("[data-toggle-task]").forEach((button) => {
    button.addEventListener("click", () => toggleTask(button.dataset.toggleTask));
  });
  spaPanel.querySelectorAll("[data-remove-task]").forEach((button) => {
    button.addEventListener("click", () => removeTask(button.dataset.removeTask));
  });
}

function renderSettingsView() {
  showPanel("Configurações", "Controle local da interface e informações do sistema.");
  spaPanel.innerHTML = `
    <div class="settings-grid">
      <button class="setting-card" data-toggle-animations>
        <strong>Animações</strong>
        <small>${state.animations ? "Ativadas" : "Desativadas"}</small>
      </button>
      <button class="setting-card" data-clear-history>
        <strong>Limpar histórico</strong>
        <small>Remove registros locais do chat no servidor.</small>
      </button>
      <div class="setting-card">
        <strong>ORION V1.1</strong>
        <small>Foundation Update. Seguro, PWA, Groq, OAuth e HUD responsivo.</small>
      </div>
      <div class="setting-card">
        <strong>Login</strong>
        <small>Google/Microsoft são ativados via variáveis OAuth no Render.</small>
      </div>
    </div>
  `;
  spaPanel.querySelector("[data-toggle-animations]").addEventListener("click", toggleAnimations);
  spaPanel.querySelector("[data-clear-history]").addEventListener("click", clearHistory);
}

async function sendMessage(message) {
  addMessage(message, "user", "entering");
  const thinking = addMessage("Orion pensando...", "assistant", "thinking entering");
  const bubble = thinking.querySelector(".bubble");
  sourceLabel.textContent = "PROCESSANDO";
  sendButton.disabled = true;
  try {
    const data = await api("/chat", {
      method: "POST",
      body: JSON.stringify({ user_id: userInput.value || defaultUserId, message }),
    });
    thinking.classList.remove("thinking");
    bubble.textContent = data.reply || data.error || "Orion nao conseguiu responder agora.";
    sourceLabel.textContent = data.source ? data.source.toUpperCase() : "ORION";
  } catch (_error) {
    thinking.classList.remove("thinking");
    bubble.textContent = "Conexão instável. Tente novamente em instantes.";
    sourceLabel.textContent = "OFFLINE";
  } finally {
    sendButton.disabled = false;
    messageInput.focus();
    scrollMessages();
  }
}

function addMessage(text, type, extraClass = "") {
  const article = document.createElement("article");
  const bubble = document.createElement("div");
  article.className = `message ${type} ${extraClass}`.trim();
  bubble.className = "bubble";
  bubble.textContent = text;
  article.appendChild(bubble);
  messages.appendChild(article);
  scrollMessages();
  return article;
}

function scrollMessages() {
  requestAnimationFrame(() => {
    messages.scrollTop = messages.scrollHeight;
  });
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
      ...(options.headers || {}),
    },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "request failed");
  return data;
}

async function loadMemory() {
  return api(`/memory?user_id=${encodeURIComponent(userInput.value || defaultUserId)}`, {
    method: "GET",
    headers: { "X-CSRF-Token": csrfToken },
  });
}

async function saveMemoryFact(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  await api("/memory", {
    method: "POST",
    body: JSON.stringify({
      user_id: userInput.value || defaultUserId,
      key: formData.get("key"),
      value: formData.get("value"),
    }),
  });
  renderMemoryView();
}

async function forgetMemoryFact(key) {
  await api(`/memory/${encodeURIComponent(key)}?user_id=${encodeURIComponent(userInput.value || defaultUserId)}`, {
    method: "DELETE",
  });
  renderMemoryView();
}

async function clearHistory() {
  await api("/history/clear", {
    method: "POST",
    body: JSON.stringify({ user_id: userInput.value || defaultUserId }),
  });
  messages.innerHTML = "";
  addMessage("Histórico limpo. Núcleo pronto para uma nova sequência.", "assistant");
  if (state.currentView === "conversations") renderConversationsView();
}

function createTask(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const title = String(formData.get("task") || "").trim();
  if (!title) return;
  state.tasks.unshift({ id: crypto.randomUUID(), title, done: false });
  saveTasks();
  renderTasksView();
}

function toggleTask(id) {
  state.tasks = state.tasks.map((task) => task.id === id ? { ...task, done: !task.done } : task);
  saveTasks();
  renderTasksView();
}

function removeTask(id) {
  state.tasks = state.tasks.filter((task) => task.id !== id);
  saveTasks();
  renderTasksView();
}

function loadTasks() {
  try {
    return JSON.parse(localStorage.getItem("orion-tasks-v11") || "[]");
  } catch (_error) {
    return [];
  }
}

function saveTasks() {
  localStorage.setItem("orion-tasks-v11", JSON.stringify(state.tasks));
}

function toggleAnimations() {
  state.animations = !state.animations;
  localStorage.setItem("orion-animations", state.animations ? "on" : "off");
  document.body.classList.toggle("no-animations", !state.animations);
  renderSettingsView();
}

function renderHistoryItem(item) {
  return `<article class="data-row ${item.role === "user" ? "is-user" : ""}"><strong>${item.role === "user" ? "Você" : "Orion"}</strong><span>${escapeHtml(item.content || "")}</span></article>`;
}

function renderMemoryItem([key, value]) {
  return `<article class="data-row"><strong>${escapeHtml(key)}</strong><span>${escapeHtml(String(value))}</span><button data-forget="${escapeHtml(key)}">Remover</button></article>`;
}

function renderTaskItem(task) {
  return `<article class="data-row ${task.done ? "done" : ""}"><strong>${escapeHtml(task.title)}</strong><span>${task.done ? "Concluída" : "Pendente"}</span><button data-toggle-task="${task.id}">${task.done ? "Reabrir" : "Concluir"}</button><button data-remove-task="${task.id}">Remover</button></article>`;
}

function emptyState(text) {
  return `<div class="empty-state">${escapeHtml(text)}</div>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

renderChatView();
