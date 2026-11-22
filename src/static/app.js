import { api, onUnauthorized, session } from "./services/api.js";
import { h, mount } from "./utils/dom.js";
import { ROLE, displayName } from "./utils/format.js";
import { AuthView } from "./components/authView.js";
import { FilterTabs, TicketList } from "./components/ticketList.js";
import { TicketForm } from "./components/ticketForm.js";
import { TicketDetail } from "./components/ticketDetail.js";

const root = document.getElementById("app");

const state = { me: null, tickets: [], stats: null, filter: "all", search: "" };
let renderToken = 0;
let shell = null;

function currentRoute() {
  const hash = location.hash || "#/";
  const match = hash.match(/^#\/ticket\/(\d+)$/);
  if (match) return { name: "detail", id: Number(match[1]) };
  if (hash === "#/new") return { name: "new" };
  return { name: "list" };
}

/* ---------- вход и выход ---------- */

function showAuth() {
  state.me = null;
  shell = null;
  mount(root, h("main", { class: "auth-page" }, AuthView({ onSuccess: start })));
}

function logout() {
  session.clear();
  location.hash = "#/";
  showAuth();
}

onUnauthorized(() => {
  session.clear();
  showAuth();
});

async function start() {
  if (!session.token) return showAuth();
  try {
    state.me = await api.me();
  } catch {
    session.clear();
    return showAuth();
  }
  buildShell();
  await refresh();
}

/* ---------- каркас приложения ---------- */

function buildShell() {
  const isAgent = state.me.role === "agent";
  let timer = null;

  const search = h("input", {
    type: "search", id: "search", placeholder: "Поиск по заявкам", "aria-label": "Поиск по заявкам",
    oninput: (event) => {
      clearTimeout(timer);
      timer = setTimeout(() => { state.search = event.target.value.trim(); loadList(); }, 250);
    },
  });

  shell = {
    filters: h("div", {}),
    list: h("div", {}),
    work: h("div", { class: "work" }),
    workspace: h("main", { class: "workspace" }),
  };

  mount(shell.workspace,
    h("section", { class: "pane pane-list", "aria-label": "Список заявок" },
      h("div", { class: "list-head" },
        h("h1", {}, isAgent ? "Все заявки" : "Мои заявки"),
        h("a", { class: "btn primary", href: "#/new" }, "Новая заявка"),
      ),
      h("div", { class: "search" }, search),
      shell.filters,
      shell.list,
    ),
    h("section", { class: "pane pane-work", "aria-label": "Заявка" }, shell.work),
  );

  mount(root,
    h("header", { class: "topbar" },
      h("span", { class: "brand" }, "Заявки"),
      h("span", { class: "who" },
        h("span", { class: "who-name" }, displayName(state.me)),
        h("span", { class: "who-role" }, ROLE[state.me.role]),
      ),
      h("button", { class: "btn bar", type: "button", onclick: logout }, "Выйти"),
    ),
    shell.workspace,
  );
}

/* ---------- данные ---------- */

async function loadList() {
  try {
    const [tickets, stats] = await Promise.all([
      api.listTickets({ status: state.filter === "all" ? undefined : state.filter, search: state.search }),
      api.stats(),
    ]);
    state.tickets = tickets;
    state.stats = stats;
    renderList();
  } catch (err) {
    mount(shell.list, h("p", { class: "form-error", role: "alert" }, err.message));
  }
}

function renderList() {
  if (!shell) return;
  const route = currentRoute();
  const filtered = state.filter !== "all" || state.search;
  mount(shell.filters, FilterTabs({
    stats: state.stats,
    active: state.filter,
    onChange: (value) => { state.filter = value; loadList(); },
  }));
  mount(shell.list, TicketList({
    tickets: state.tickets,
    selectedId: route.name === "detail" ? route.id : null,
    showAuthor: state.me.role === "agent",
    emptyText: filtered
      ? "Ничего не найдено. Измените фильтр или строку поиска."
      : "Заявок пока нет. Нажмите «Новая заявка» и опишите проблему.",
  }));
}

async function renderRoute() {
  if (!shell) return;
  const route = currentRoute();
  const token = ++renderToken;
  shell.workspace.dataset.view = route.name;

  if (route.name === "new") {
    mount(shell.work, TicketForm({
      onCreated: async (ticket) => {
        location.hash = `#/ticket/${ticket.id}`;
        await loadList();
      },
    }));
    return;
  }

  if (route.name === "list") {
    mount(shell.work, h("p", { class: "placeholder" },
      "Выберите заявку в списке или создайте новую."));
    return;
  }

  try {
    const ticket = await api.getTicket(route.id);
    if (token !== renderToken) return; // пользователь уже ушёл на другую заявку
    mount(shell.work, TicketDetail({ ticket, me: state.me, onChanged: refresh }));
  } catch (err) {
    if (token !== renderToken) return;
    mount(shell.work, h("div", { class: "detail" },
      h("a", { class: "back", href: "#/" }, "К списку заявок"),
      h("p", { class: "form-error", role: "alert" }, err.message),
    ));
  }
}

async function refresh() {
  await Promise.all([loadList(), renderRoute()]);
}

window.addEventListener("hashchange", () => {
  if (!shell) return;
  renderList();
  renderRoute();
});

start();
