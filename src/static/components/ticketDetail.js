import { h } from "../utils/dom.js";
import { api } from "../services/api.js";
import { PRIORITY, ROLE, STATUS, displayName, formatDate } from "../utils/format.js";
import { StatusLabel } from "./statusLabel.js";

export function TicketDetail({ ticket, me, onChanged }) {
  const isAgent = me.role === "agent";
  const isAuthor = ticket.author.id === me.id;
  const closed = ticket.status === "closed";

  const error = h("p", { class: "form-error", role: "alert", hidden: true });
  const fail = (err) => { error.textContent = err.message; error.hidden = false; };

  async function patch(changes) {
    error.hidden = true;
    try {
      await api.updateTicket(ticket.id, changes);
      await onChanged();
    } catch (err) {
      fail(err);
    }
  }

  const facts = h("dl", { class: "facts" },
    fact("Статус", StatusLabel(ticket.status)),
    fact("Приоритет", PRIORITY[ticket.priority]),
    fact("Автор", displayName(ticket.author)),
    fact("Исполнитель", ticket.assignee ? displayName(ticket.assignee) : "Не назначен"),
    fact("Создана", formatDate(ticket.created_at)),
    fact("Обновлена", formatDate(ticket.updated_at)),
  );

  function fact(label, value) {
    return h("div", {}, h("dt", {}, label), h("dd", {}, value));
  }

  function controls() {
    if (isAgent) {
      const mine = ticket.assignee && ticket.assignee.id === me.id;
      const status = h("select", {
        id: "status", value: ticket.status,
        onchange: (e) => patch({ status: e.target.value }),
      }, Object.entries(STATUS).map(([value, label]) => h("option", { value }, label)));
      status.value = ticket.status;
      const priority = h("select", {
        id: "priority-edit", value: ticket.priority,
        onchange: (e) => patch({ priority: e.target.value }),
      }, Object.entries(PRIORITY).map(([value, label]) => h("option", { value }, label)));
      priority.value = ticket.priority;

      return h("div", { class: "controls" },
        h("div", { class: "field" }, h("label", { for: "status" }, "Статус"), status),
        h("div", { class: "field" }, h("label", { for: "priority-edit" }, "Приоритет"), priority),
        h("button", {
          class: "btn ghost", type: "button",
          onclick: () => patch(mine
            ? { assignee_id: null }
            : { assignee_id: me.id, status: ticket.status === "new" ? "in_progress" : ticket.status }),
        }, mine ? "Снять с себя" : "Взять в работу"),
      );
    }
    if (!isAuthor) return null;
    return h("div", { class: "controls" },
      closed ? null : h("button", {
        class: "btn ghost", type: "button", onclick: () => patch({ status: "closed" }),
      }, "Закрыть заявку"),
      ticket.status === "resolved" || closed ? h("button", {
        class: "btn ghost", type: "button", onclick: () => patch({ status: "new" }),
      }, "Открыть заново") : null,
    );
  }

  const textarea = h("textarea", {
    id: "comment", rows: 3, maxlength: 2000, required: true, placeholder: "Напишите комментарий",
  });
  const send = h("button", { class: "btn primary", type: "submit" }, "Отправить комментарий");
  const commentForm = closed
    ? h("p", { class: "note" }, isAgent
        ? "Заявка закрыта. Смените статус, чтобы писать комментарии."
        : "Заявка закрыта. Откройте её заново, чтобы написать комментарий.")
    : h("form", {
        class: "comment-form",
        novalidate: true,
        onsubmit: async (event) => {
          event.preventDefault();
          const text = textarea.value.trim();
          if (!text) return;
          error.hidden = true;
          send.disabled = true;
          try {
            await api.addComment(ticket.id, { text });
            await onChanged();
          } catch (err) {
            fail(err);
            send.disabled = false;
          }
        },
      },
        h("label", { for: "comment" }, "Новый комментарий"),
        textarea,
        send,
      );

  return h("article", { class: "detail" },
    h("a", { class: "back", href: "#/" }, "К списку заявок"),
    h("p", { class: "detail-num" }, `Заявка №${ticket.id}`),
    h("h2", {}, ticket.title),
    facts,
    h("p", { class: "description" }, ticket.description),
    controls(),
    error,
    h("section", { class: "comments", "aria-labelledby": "comments-title" },
      h("h3", { id: "comments-title" }, `Комментарии (${ticket.comments.length})`),
      ticket.comments.length
        ? h("ol", {}, ticket.comments.map((comment) =>
            h("li", { class: comment.author.role === "agent" ? "comment by-agent" : "comment" },
              h("p", { class: "comment-head" },
                h("strong", {}, displayName(comment.author)),
                h("span", {}, ROLE[comment.author.role] || ""),
                h("span", {}, formatDate(comment.created_at)),
              ),
              h("p", { class: "comment-text" }, comment.text),
            )))
        : h("p", { class: "note" }, "Комментариев пока нет."),
      commentForm,
    ),
  );
}
