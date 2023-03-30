from httpx import AsyncClient


async def test_bad_get_my_notifications_unauthorized(ac: AsyncClient):
    response = await ac.get("/notifications/my/")
    assert response.status_code == 403


async def test_get_my_notifications_user_one(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/notifications/my/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]['status'] == 'sent'
    assert response.json()[1]['status'] == 'sent'
    assert response.json()[1]['created_by'] == 1


async def test_bad_get_notification_not_found(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/notifications/100/", headers=headers)
    assert response.status_code == 404


async def test_bad_get_notification_forbidden(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/notifications/3/", headers=headers)
    assert response.status_code == 403


async def test_see_notification_one(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/notifications/1/", headers=headers)
    assert response.status_code == 200
    assert response.json()['status'] == 'seen'


async def test_get_my_notifications_after_seeing_one(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/notifications/my/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['status'] == 'sent'


async def test_get_my_notifications_with_seen_true(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/notifications/my/?seen=true", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]['status'] == 'sent'
    assert response.json()[1]['status'] == 'seen'
