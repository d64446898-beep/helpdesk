import { h } from "../utils/dom.js";
import { PRIORITY, displayName, formatDate } from "../utils/format.js";
import { StatusLabel } from "./statusLabel.js";

const FILTERS = [
  ["all", "Все", "total"],
  ["new", "Новые", "new"],
  ["in_progress", "В работе", "in_progress"],
  ["resolved", "Решены", "resolved"],
  ["closed", "Закрыты", "closed"],
];

export function FilterTabs({ stats, active, onChange }) {
  return h("div", { class: "filters", role: "group", "aria-label": "Фильтр по статусу" },
    FILTERS.map(([value, label, key]) =>
      h("button", {
        type: "button",
        class: "filter",
        "aria-pressed": String(value === active),
        onclick: () => onChange(value),
      },
        label,
        h("span", { class: "count" }, stats ? stats[key] : 0),
      )),
  );
}

export function TicketList({ tickets, selectedId, showAuthor, emptyText }) {
  if (!tickets.length) {
    return h("p", { class: "empty" }, emptyText);
  }
  return h("ul", { class: "ticket-list" }, tickets.map((ticket) =>
    h("li", {},
      h("a", {
        class: "ticket-row",
        href: `#/ticket/${ticket.id}`,
        "data-status": ticket.status,
        "aria-current": ticket.id === selectedId ? "true" : null,
      },
        h("span", { class: "rail", "aria-hidden": "true" }),
        h("span", { class: "ticket-body" },
          h("span", { class: "ticket-title" },
            h("span", { class: "num" }, `№${ticket.id}`), " ", ticket.title),
          h("span", { class: "meta" },
            StatusLabel(ticket.status),
            ticket.priority === "high"
              ? h("span", { class: "flag" }, `${PRIORITY.high} приоритет`) : null,
            showAuthor ? h("span", {}, displayName(ticket.author)) : null,
            h("span", {}, formatDate(ticket.updated_at)),
            ticket.comments_count
              ? h("span", {}, `Комментарии: ${ticket.comments_count}`) : null,
          ),
        ),
      ),
    ),
  ));
}
