// Обёртка над fetch: подставляет токен и превращает ошибки в понятные сообщения.
const TOKEN_KEY = "helpdesk_token";

export const session = {
  get token() {
    try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
  },
  save(token) {
    try { localStorage.setItem(TOKEN_KEY, token); } catch { /* хранилище недоступно */ }
  },
  clear() {
    try { localStorage.removeItem(TOKEN_KEY); } catch { /* хранилище недоступно */ }
  },
};

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

let unauthorizedHandler = () => {};
export function onUnauthorized(handler) {
  unauthorizedHandler = handler;
}

async function request(method, path, body, { auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth && session.token) headers["Authorization"] = `Bearer ${session.token}`;

  let response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Нет связи с сервером. Проверьте, что он запущен.");
  }

  let data = null;
  try { data = await response.json(); } catch { /* пустой ответ */ }

  if (!response.ok) {
    if (response.status === 401 && auth) unauthorizedHandler();
    const message = data && typeof data.detail === "string"
      ? data.detail
      : "Что-то пошло не так. Попробуйте ещё раз.";
    throw new ApiError(response.status, message);
  }
  return data;
}

export const api = {
  register: (body) => request("POST", "/auth/register", body, { auth: false }),
  login: (body) => request("POST", "/auth/login", body, { auth: false }),
  me: () => request("GET", "/auth/me"),

  listTickets({ status, search } = {}) {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (search) params.set("search", search);
    const query = params.toString();
    return request("GET", `/tickets${query ? "?" + query : ""}`);
  },
  stats: () => request("GET", "/tickets/stats"),
  getTicket: (id) => request("GET", `/tickets/${id}`),
  createTicket: (body) => request("POST", "/tickets", body),
  updateTicket: (id, body) => request("PATCH", `/tickets/${id}`, body),
  addComment: (id, body) => request("POST", `/tickets/${id}/comments`, body),
};
