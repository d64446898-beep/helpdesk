# Архитектура

## Компоненты

```mermaid
flowchart LR
    subgraph Browser["Браузер (src/static)"]
        UI["components: вход, список, форма, заявка"]
        API["services/api.js: fetch и токен"]
        UI --> API
    end

    subgraph Server["Сервер FastAPI (src)"]
        MAIN["main.py: приложение, ошибки, раздача клиента"]
        R["routers: auth, tickets"]
        D["deps.py: текущий пользователь"]
        S["services: auth_service, ticket_service"]
        SEC["security.py: PBKDF2, JWT"]
        M["models.py и schemas.py"]
        MAIN --> R
        R --> D
        R --> S
        D --> SEC
        S --> SEC
        S --> M
    end

    DB[("SQLite: helpdesk.db")]

    API -- "HTTP, JSON, Bearer-токен" --> MAIN
    M --> DB
```

## Слои сервера

| Слой | Файлы | Ответственность |
|------|-------|-----------------|
| Маршруты | `routers/` | Принимают запрос, проверяют формат данных через схемы, вызывают сервисы |
| Сервисы | `services/` | Правила предметной области: кто что видит и меняет, допустимые переходы статусов |
| Данные | `models.py`, `database.py` | Таблицы и подключение к БД |
| Безопасность | `security.py`, `deps.py` | Хэширование паролей, выпуск и проверка токенов, определение текущего пользователя |
| Ошибки | `utils/errors.py`, `main.py` | Единый формат ошибок `{"detail": "..."}` на русском языке |

## Модель данных

```mermaid
erDiagram
    USERS ||--o{ TICKETS : "автор"
    USERS ||--o{ TICKETS : "исполнитель"
    USERS ||--o{ COMMENTS : "пишет"
    TICKETS ||--o{ COMMENTS : "содержит"

    USERS {
        int id PK
        string username UK
        string full_name
        string password_hash
        string role "user или agent"
    }
    TICKETS {
        int id PK
        string title
        text description
        string status "new, in_progress, resolved, closed"
        string priority "low, normal, high"
        int author_id FK
        int assignee_id FK
        datetime created_at
        datetime updated_at
    }
    COMMENTS {
        int id PK
        int ticket_id FK
        int author_id FK
        text text
        datetime created_at
    }
```

## Сценарий запроса

1. Клиент отправляет `POST /api/auth/login`, сервер проверяет пароль и возвращает JWT.
2. Токен сохраняется в браузере и добавляется в заголовок каждого следующего запроса.
3. `deps.get_current_user` расшифровывает токен и загружает пользователя; без валидного токена возвращается 401.
4. Сервис проверяет права (роль, авторство) и выполняет действие; при нарушении возвращает 403, 404 или 409.

## Права доступа

| Действие | Сотрудник | Поддержка |
|----------|-----------|-----------|
| Видеть заявки | только свои | все |
| Создать заявку | да | да |
| Комментировать | в своих заявках | в любых |
| Менять статус | закрыть свою или открыть заново | любой |
| Менять приоритет и исполнителя | нет | да |

## Клиент

Одностраничное приложение без сборки. Маршрутизация по `location.hash` (`#/`, `#/new`, `#/ticket/<id>`). Все элементы создаются через `utils/dom.js` без `innerHTML`, поэтому пользовательский текст не может внедрить разметку. На узком экране показывается одна панель (список или заявка), на широком обе.
