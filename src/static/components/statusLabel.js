import { h } from "../utils/dom.js";
import { STATUS } from "../utils/format.js";

// Статус: цветная точка и подпись (цвет не единственный носитель смысла).
export function StatusLabel(status) {
  return h("span", { class: "status", "data-status": status }, STATUS[status] || status);
}
