from httpx import AsyncClient


async def test_create_company_unauthorized(ac: AsyncClient):
    payload = {
        "company_name": "company1",
        "company_description": "string"
    }
    response = await ac.post("/companies/", json=payload)
    assert response.status_code == 403


async def test_bad_create_company__no_name(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "company_name": "",
        "company_description": "company_description"
    }
    response = await ac.post("/companies/", json=payload, headers=headers)
    assert response.status_code == 422


async def test_create_company_one(users_tokens, ac: AsyncClient):

    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "company_name": "test_company_1",
        "company_description": "company_description_1"
    }
    response = await ac.post("/companies/", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json().get("result").get("company_id") == 1


async def test_create_company_two(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "company_name": "test_company_2",
    }
    response = await ac.post("/companies/", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json().get("result").get("company_id") == 2


async def test_create_company_three(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "company_name": "test_company_3",
    }
    response = await ac.post("/companies/", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json().get("result").get("company_id") == 3


async def test_get_all_companies(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/companies/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get("result").get('companies')) == 3


async def test_bad_get_company_by_id_not_found(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/companies/4/", headers=headers)
    assert response.status_code == 404


async def test_get_company_by_id_one(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/companies/1/", headers=headers)
    assert response.status_code == 200
    assert response.json().get("result").get("company_id") == 1
    assert response.json().get("result").get("company_name") == "test_company_1"
    assert response.json().get("result").get("company_description") == "company_description_1"
    assert response.json().get("result").get("company_owner_id") == 1


async def test_get_company_by_id_tw(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/companies/2/", headers=headers)
    assert response.status_code == 200
    assert response.json().get("result").get("company_id") == 2
    assert response.json().get("result").get("company_name") == "test_company_2"
    assert response.json().get("result").get("company_description") == None
    assert response.json().get("result").get("company_owner_id") == 1


async def test_bad_update_company__unauthorized(ac: AsyncClient):
    payload = {
        "company_name": "company_name_1_NEW",
        "company_description": "company_description_1_NEW"
    }
    response = await ac.put("/companies/1/", json=payload)
    assert response.status_code == 403


async def test_bad_update_company__not_found(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "company_name": "company_name_1_NEW",
        "company_description": "company_description_1_NEW"
    }
    response = await ac.put("/companies/100/", json=payload, headers=headers)
    assert response.status_code == 404


async def test_update_company(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "company_name": "company_name_1_NEW",
        "company_description": "company_description_1_NEW"
    }
    response = await ac.put("/companies/1/", json=payload, headers=headers)
    assert response.status_code == 200


async def test_get_company_by_id_one_updated(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/companies/1/", headers=headers)
    assert response.status_code == 200
    assert response.json().get("result").get("company_id") == 1
    assert response.json().get("result").get("company_name") == "company_name_1_NEW"
    assert response.json().get("result").get("company_description") == "company_description_1_NEW"
    assert response.json().get("result").get("company_owner_id") == 1


async def test_bad_delete_company_one__user_not_owner(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.delete("/companies/1/", headers=headers)
    assert response.status_code == 403


async def test_delete_company_one(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.delete("/companies/1/", headers=headers)
    assert response.status_code == 204


async def test_get_all_companies_after_not_delete(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/companies/", headers=headers)
    print(response.json())
    assert response.status_code == 200
    assert len(response.json().get("result").get('companies')) == 2
