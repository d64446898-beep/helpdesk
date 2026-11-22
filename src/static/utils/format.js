export const STATUS = {
  new: "Новая",
  in_progress: "В работе",
  resolved: "Решена",
  closed: "Закрыта",
};

export const PRIORITY = {
  low: "Низкий",
  normal: "Обычный",
  high: "Высокий",
};

export const ROLE = {
  user: "сотрудник",
  agent: "поддержка",
};

// Сервер отдаёт время UTC без часового пояса, добавляем «Z».
export function parseDate(value) {
  const hasZone = /[zZ]$|[+-]\d\d:?\d\d$/.test(value);
  return new Date(hasZone ? value : value + "Z");
}

export function formatDate(value) {
  return parseDate(value).toLocaleString("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function displayName(user) {
  return user.full_name || user.username;
}
