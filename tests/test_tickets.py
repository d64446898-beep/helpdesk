"""Тесты заявок: создание, доступ, статусы, комментарии, статистика."""

NEW_TICKET = {"title": "Не работает мышь", "description": "Курсор не двигается", "priority": "high"}


def create(client, headers, **overrides):
    res = client.post("/api/tickets", json={**NEW_TICKET, **overrides}, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_create_ticket(client, user_headers):
    ticket = create(client, user_headers)
    assert ticket["status"] == "new"
    assert ticket["priority"] == "high"
    assert ticket["author"]["username"] == "ivan"
    assert ticket["assignee"] is None


def test_create_ticket_validation(client, user_headers):
    res = client.post("/api/tickets", json={"title": "ab", "description": ""}, headers=user_headers)
    assert res.status_code == 422
    assert "тема" in res.json()["detail"]


def test_create_ticket_rejects_blank_text(client, user_headers):
    res = client.post("/api/tickets", json={"title": "   ", "description": "x"}, headers=user_headers)
    assert res.status_code == 422


def test_user_sees_only_own_tickets(client, user_headers, other_headers):
    create(client, user_headers, title="Заявка Ивана")
    create(client, other_headers, title="Заявка Ольги")
    titles = [t["title"] for t in client.get("/api/tickets", headers=user_headers).json()]
    assert titles == ["Заявка Ивана"]


def test_agent_sees_all_tickets(client, user_headers, other_headers, agent_headers):
    create(client, user_headers)
    create(client, other_headers)
    assert len(client.get("/api/tickets", headers=agent_headers).json()) == 2


def test_user_cannot_open_foreign_ticket(client, user_headers, other_headers):
    ticket = create(client, user_headers)
    res = client.get(f"/api/tickets/{ticket['id']}", headers=other_headers)
    assert res.status_code == 403


def test_ticket_not_found(client, user_headers):
    assert client.get("/api/tickets/999", headers=user_headers).status_code == 404


def test_filter_by_status_and_search(client, user_headers, agent_headers):
    first = create(client, user_headers, title="Принтер не печатает")
    create(client, user_headers, title="Нет интернета")
    client.patch(f"/api/tickets/{first['id']}", json={"status": "in_progress"}, headers=agent_headers)

    in_progress = client.get("/api/tickets?status=in_progress", headers=user_headers).json()
    assert [t["id"] for t in in_progress] == [first["id"]]

    found = client.get("/api/tickets?search=интернет", headers=user_headers).json()
    assert [t["title"] for t in found] == ["Нет интернета"]

    assert client.get("/api/tickets?status=bogus", headers=user_headers).status_code == 422


def test_agent_changes_status_priority_and_assignee(client, user_headers, agent_headers):
    ticket = create(client, user_headers)
    agent_id = client.get("/api/auth/me", headers=agent_headers).json()["id"]
    res = client.patch(
        f"/api/tickets/{ticket['id']}",
        json={"status": "in_progress", "priority": "low", "assignee_id": agent_id},
        headers=agent_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "in_progress"
    assert body["priority"] == "low"
    assert body["assignee"]["id"] == agent_id


def test_agent_can_unassign(client, user_headers, agent_headers):
    ticket = create(client, user_headers)
    agent_id = client.get("/api/auth/me", headers=agent_headers).json()["id"]
    url = f"/api/tickets/{ticket['id']}"
    client.patch(url, json={"assignee_id": agent_id}, headers=agent_headers)
    res = client.patch(url, json={"assignee_id": None}, headers=agent_headers)
    assert res.json()["assignee"] is None


def test_cannot_assign_regular_user(client, user_headers, other_headers, agent_headers):
    ticket = create(client, user_headers)
    other_id = client.get("/api/auth/me", headers=other_headers).json()["id"]
    res = client.patch(f"/api/tickets/{ticket['id']}", json={"assignee_id": other_id},
                       headers=agent_headers)
    assert res.status_code == 422


def test_author_can_close_and_reopen_own_ticket(client, user_headers):
    ticket = create(client, user_headers)
    url = f"/api/tickets/{ticket['id']}"
    assert client.patch(url, json={"status": "closed"}, headers=user_headers).json()["status"] == "closed"
    assert client.patch(url, json={"status": "new"}, headers=user_headers).json()["status"] == "new"


def test_author_cannot_set_other_statuses_or_priority(client, user_headers):
    ticket = create(client, user_headers)
    url = f"/api/tickets/{ticket['id']}"
    assert client.patch(url, json={"status": "resolved"}, headers=user_headers).status_code == 403
    assert client.patch(url, json={"priority": "low"}, headers=user_headers).status_code == 403


def test_comments_flow(client, user_headers, agent_headers):
    ticket = create(client, user_headers)
    url = f"/api/tickets/{ticket['id']}/comments"
    assert client.post(url, json={"text": "Проверьте кабель"}, headers=agent_headers).status_code == 201
    assert client.post(url, json={"text": "Помогло, спасибо"}, headers=user_headers).status_code == 201

    detail = client.get(f"/api/tickets/{ticket['id']}", headers=user_headers).json()
    assert [c["text"] for c in detail["comments"]] == ["Проверьте кабель", "Помогло, спасибо"]
    assert detail["comments"][0]["author"]["role"] == "agent"
    assert detail["comments_count"] == 2


def test_comment_validation(client, user_headers):
    ticket = create(client, user_headers)
    res = client.post(f"/api/tickets/{ticket['id']}/comments", json={"text": "  "}, headers=user_headers)
    assert res.status_code == 422


def test_cannot_comment_on_foreign_ticket(client, user_headers, other_headers):
    ticket = create(client, user_headers)
    res = client.post(f"/api/tickets/{ticket['id']}/comments", json={"text": "привет"},
                      headers=other_headers)
    assert res.status_code == 403


def test_cannot_comment_on_closed_ticket(client, user_headers):
    ticket = create(client, user_headers)
    client.patch(f"/api/tickets/{ticket['id']}", json={"status": "closed"}, headers=user_headers)
    res = client.post(f"/api/tickets/{ticket['id']}/comments", json={"text": "ещё вопрос"},
                      headers=user_headers)
    assert res.status_code == 409


def test_stats_are_scoped_to_user(client, user_headers, other_headers, agent_headers):
    first = create(client, user_headers)
    create(client, user_headers)
    create(client, other_headers)
    client.patch(f"/api/tickets/{first['id']}", json={"status": "resolved"}, headers=agent_headers)

    mine = client.get("/api/tickets/stats", headers=user_headers).json()
    assert mine == {"total": 2, "new": 1, "in_progress": 0, "resolved": 1, "closed": 0}

    everything = client.get("/api/tickets/stats", headers=agent_headers).json()
    assert everything["total"] == 3
