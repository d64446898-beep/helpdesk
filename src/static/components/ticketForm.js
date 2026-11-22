import { h } from "../utils/dom.js";
import { api } from "../services/api.js";

export function TicketForm({ onCreated }) {
  const error = h("p", { class: "form-error", role: "alert", hidden: true });
  const title = h("input", {
    id: "title", name: "title", required: true, maxlength: 150, autocomplete: "off",
    placeholder: "Например: не включается монитор",
  });
  const description = h("textarea", {
    id: "description", name: "description", rows: 6, required: true, maxlength: 5000,
    placeholder: "Что произошло, где и когда. Что уже пробовали сделать.",
  });
  const priority = h("select", { id: "priority", name: "priority", value: "normal" },
    h("option", { value: "low" }, "Низкий: можно подождать"),
    h("option", { value: "normal" }, "Обычный"),
    h("option", { value: "high" }, "Высокий: работа остановилась"),
  );
  priority.value = "normal";
  const submit = h("button", { class: "btn primary", type: "submit" }, "Отправить заявку");

  return h("form", {
    class: "ticket-form",
    novalidate: true,
    onsubmit: async (event) => {
      event.preventDefault();
      error.hidden = true;
      submit.disabled = true;
      try {
        const ticket = await api.createTicket({
          title: title.value.trim(),
          description: description.value.trim(),
          priority: priority.value,
        });
        await onCreated(ticket);
      } catch (err) {
        error.textContent = err.message;
        error.hidden = false;
        submit.disabled = false;
      }
    },
  },
    h("a", { class: "back", href: "#/" }, "К списку заявок"),
    h("h2", {}, "Новая заявка"),
    h("div", { class: "field" }, h("label", { for: "title" }, "Тема"), title),
    h("div", { class: "field" }, h("label", { for: "description" }, "Что случилось"), description),
    h("div", { class: "field" }, h("label", { for: "priority" }, "Приоритет"), priority),
    error,
    submit,
  );
}
