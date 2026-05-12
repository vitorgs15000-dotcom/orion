const state = {
  currentView: "chat",
  tasks: loadTasks(),
  animations: localStorage.getItem("orion-animations") !== "off",
  voice: localStorage.getItem("orion-voice") === "on",
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
const orb = document.querySelector("#orion-orb");
const orbPanel = document.querySelector("#orb-panel");
const orbClose = document.querySelector("#orb-close");
const orbForm = document.querySelector("#orb-form");
const orbInput = document.querySelector("#orb-input");
const orbMessages = document.querySelector("#orb-messages");
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
  addMessage("Novo chat iniciado. Núcleo pronto para uma nova sequência.", "assistant");
  sourceLabel.textContent = "ORION Legacy IA";
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

if (orb && orbPanel) {
  initOrbOverlay();
}

function setView(view) {
  state.currentView = view;
  sidebar.classList.remove("open");
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });

  const renderers = {
    chat: renderChatView,
    conversations: renderConversationsView,
    memory: renderMemoryView,
    tasks: renderTasksView,
    settings: renderSettingsView,
  };
  (renderers[view] || renderChatView)();
}

function showPanel(title, subtitle, kicker = "ORION Legacy Edition") {
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
  viewKicker.textContent = "ORION Legacy Edition ONLINE";
  viewTitle.textContent = "Olá, eu sou o Orion.";
  viewSubtitle.textContent = "Sistema pessoal de IA criado por lava_rip2012.";
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
  showPanel("Memória", "Informações pessoais e contexto persistente.");
  const data = await loadMemory();
  const profile = data.profile || {};
  const entries = Object.entries(profile);
  spaPanel.innerHTML = `
    <form class="inline-form" id="memory-form">
      <input name="key" placeholder="chave, exemplo: foco" maxlength="48" required />
      <input name="value" placeholder="valor, exemplo: evoluir o Orion" maxlength="300" required />
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
  showPanel("Configurações", "Controle local da interface e informações da edição Legacy.");
  spaPanel.innerHTML = `
    <div class="settings-grid">
      <button class="setting-card" data-toggle-animations>
        <strong>Animações</strong>
        <small>${state.animations ? "Ativadas" : "Desativadas"}</small>
      </button>
      <button class="setting-card" data-toggle-voice>
        <strong>Voz Orion</strong>
        <small>${voiceSupported() ? (state.voice ? "Ativada" : "Desativada") : "Indisponível neste navegador"}</small>
      </button>
      <button class="setting-card" data-clear-history>
        <strong>Limpar histórico</strong>
        <small>Remove registros do chat no servidor.</small>
      </button>
      <div class="setting-card">
        <strong>ORION Legacy Edition</strong>
        <small>Versão histórica privada, criada para lava_rip2012 e família.</small>
      </div>
      <div class="setting-card">
        <strong>História</strong>
        <small>Projeto iniciado há aproximadamente 1 mês e preservado como marco do Orion.</small>
      </div>
      <div class="setting-card">
        <strong>Login</strong>
        <small>Google/Microsoft são ativados via variáveis OAuth no servidor privado.</small>
      </div>
      <div class="setting-card">
        <strong>Android</strong>
        <small>PWA instalável. APK/TWA pode ser gerado com Bubblewrap quando o domínio final estiver pronto.</small>
      </div>
      <div class="setting-card">
        <strong>Orb</strong>
        <small>A orb funciona dentro do PWA. Sobreposição com app fechado exige app Android nativo.</small>
      </div>
    </div>
  `;
  spaPanel.querySelector("[data-toggle-animations]").addEventListener("click", toggleAnimations);
  spaPanel.querySelector("[data-toggle-voice]").addEventListener("click", toggleVoice);
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
    bubble.textContent = data.reply || data.error || "Orion não conseguiu responder agora.";
    speakOrion(bubble.textContent);
    sourceLabel.textContent = data.source ? data.source.toUpperCase() : "ORION Legacy";
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

async function sendOverlayMessage(message) {
  addOrbMessage(message, "user");
  const thinking = addOrbMessage("Orion pensando...", "assistant thinking");
  try {
    const data = await api("/chat", {
      method: "POST",
      body: JSON.stringify({ user_id: userInput.value || defaultUserId, message }),
    });
    thinking.classList.remove("thinking");
    thinking.textContent = data.reply || data.error || "Orion não conseguiu responder agora.";
    speakOrion(thinking.textContent);
  } catch (_error) {
    thinking.classList.remove("thinking");
    thinking.textContent = "Conexão instável. Tente novamente.";
  }
  scrollOrbMessages();
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

function initOrbOverlay() {
  let drag = null;
  const saved = loadOrbPosition();
  if (saved) {
    orb.style.left = `${saved.x}px`;
    orb.style.top = `${saved.y}px`;
    orb.style.right = "auto";
    orb.style.bottom = "auto";
  }

  orb.addEventListener("click", () => {
    if (drag?.moved) return;
    orbPanel.hidden = !orbPanel.hidden;
    if (!orbPanel.hidden) orbInput.focus();
  });

  orbClose?.addEventListener("click", () => {
    orbPanel.hidden = true;
  });

  orbForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = orbInput.value.trim();
    if (!message) return;
    orbInput.value = "";
    await sendOverlayMessage(message);
  });

  orb.addEventListener("pointerdown", (event) => {
    drag = {
      startX: event.clientX,
      startY: event.clientY,
      left: orb.offsetLeft,
      top: orb.offsetTop,
      moved: false,
    };
    orb.setPointerCapture(event.pointerId);
  });

  orb.addEventListener("pointermove", (event) => {
    if (!drag) return;
    const dx = event.clientX - drag.startX;
    const dy = event.clientY - drag.startY;
    if (Math.abs(dx) + Math.abs(dy) > 8) drag.moved = true;
    const x = clamp(drag.left + dx, 8, window.innerWidth - orb.offsetWidth - 8);
    const y = clamp(drag.top + dy, 8, window.innerHeight - orb.offsetHeight - 8);
    orb.style.left = `${x}px`;
    orb.style.top = `${y}px`;
    orb.style.right = "auto";
    orb.style.bottom = "auto";
  });

  orb.addEventListener("pointerup", () => {
    if (!drag) return;
    saveOrbPosition(orb.offsetLeft, orb.offsetTop);
    setTimeout(() => {
      drag = null;
    }, 0);
  });
}

function addOrbMessage(text, type) {
  const item = document.createElement("article");
  item.className = `orb-message ${type}`;
  item.textContent = text;
  orbMessages.appendChild(item);
  scrollOrbMessages();
  return item;
}

function scrollOrbMessages() {
  requestAnimationFrame(() => {
    orbMessages.scrollTop = orbMessages.scrollHeight;
  });
}

function loadOrbPosition() {
  try {
    return JSON.parse(localStorage.getItem("orion-orb-position") || "null");
  } catch (_error) {
    return null;
  }
}

function saveOrbPosition(x, y) {
  localStorage.setItem("orion-orb-position", JSON.stringify({ x, y }));
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
      ...(options.headers || {}),
    },
  });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : { error: "Resposta inesperada do servidor." };
  if (response.status === 401) {
    window.location.href = "/private-login";
    throw new Error("Acesso privado necessário.");
  }
  if (!response.ok) throw new Error(data.error || "Falha na solicitação.");
  return data;
}

async function loadMemory() {
  return api(`/memory?user_id=${encodeURIComponent(userInput.value || defaultUserId)}`, {
    method: "GET",
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
    return JSON.parse(localStorage.getItem("orion-tasks-legacy") || "[]");
  } catch (_error) {
    return [];
  }
}

function saveTasks() {
  localStorage.setItem("orion-tasks-legacy", JSON.stringify(state.tasks));
}

function toggleAnimations() {
  state.animations = !state.animations;
  localStorage.setItem("orion-animations", state.animations ? "on" : "off");
  document.body.classList.toggle("no-animations", !state.animations);
  renderSettingsView();
}

function toggleVoice() {
  if (!voiceSupported()) return;
  state.voice = !state.voice;
  localStorage.setItem("orion-voice", state.voice ? "on" : "off");
  if (state.voice) {
    speakOrion("Orion online. Voz sintética ativada.");
  } else {
    window.speechSynthesis.cancel();
  }
  renderSettingsView();
}

function voiceSupported() {
  return "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
}

function speakOrion(text) {
  if (!state.voice || !voiceSupported()) return;
  const cleanText = String(text || "")
    .replace(/\s+/g, " ")
    .replace(/[<>]/g, "")
    .trim()
    .slice(0, 420);
  if (!cleanText) return;

  const utterance = new SpeechSynthesisUtterance(cleanText);
  const voices = window.speechSynthesis.getVoices();
  utterance.voice = pickOrionVoice(voices);
  utterance.lang = utterance.voice?.lang || "pt-BR";
  utterance.rate = 0.92;
  utterance.pitch = 0.82;
  utterance.volume = 0.92;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

function pickOrionVoice(voices) {
  const preferred = voices.find((voice) => /pt-BR/i.test(voice.lang) && /male|mascul/i.test(voice.name));
  return preferred
    || voices.find((voice) => /pt-BR/i.test(voice.lang))
    || voices.find((voice) => /pt/i.test(voice.lang))
    || voices[0]
    || null;
}

function renderHistoryItem(item) {
  return `<article class="data-row ${item.role === "user" ? "is-user" : ""}"><strong>${item.role === "user" ? "Você" : "Orion"}</strong><span>${escapeHtml(item.content || "")}</span></article>`;
}

function renderMemoryItem([key, value]) {
  return `<article class="data-row"><strong>${escapeHtml(key)}</strong><span>${escapeHtml(JSON.stringify(value))}</span><button data-forget="${escapeHtml(key)}">Remover</button></article>`;
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
