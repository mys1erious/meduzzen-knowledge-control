from httpx import AsyncClient

# send request

async def test_send_request_not_auth(ac: AsyncClient):
    payload = {
        "to_company_id": 0,
        "invite_message": "string"
    }
    response = await ac.post("/requests/", json=payload)
    assert response.status_code == 403
    assert response.json().get('detail') == "Not authenticated"


async def test_send_request_not_found_company(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "to_company_id": 100,
        "invite_message": "string"
    }
    response = await ac.post("/requests/", json=payload, headers=headers)
    assert response.status_code == 404
    assert response.json().get('detail') == 'This company not found'


async def test_send_request_from_owner(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "to_company_id": 1,
        "invite_message": "string"
    }
    response = await ac.post("/requests/", json=payload, headers=headers)
    assert response.status_code == 400
    assert response.json().get('detail') == "User is already a member of the company"


async def test_send_request_one_success(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "to_company_id": 2,
        "invite_message": "string"
    }
    response = await ac.post("/requests/", json=payload, headers=headers)
    assert response.status_code == 400
    assert response.json().get('detail') == "User is already a member of the company"


async def test_send_request_two_success(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    payload = {
        "to_company_id": 1,
        "invite_message": "string"
    }
    response = await ac.post("/requests/", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json().get('detail') == "success"


async def test_send_request_three_success(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test3@test.com']}",
    }
    payload = {
        "to_company_id": 1,
        "invite_message": "string"
    }
    response = await ac.post("/requests/", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json().get('detail') == "success"


async def test_send_request_exist(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    payload = {
        "to_company_id": 1,
        "invite_message": "string"
    }
    response = await ac.post("/requests/", json=payload, headers=headers)
    assert response.status_code == 400
    assert response.json().get('detail') == "Request already sent"


async def test_send_request_four_success(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test4@test.com']}",
    }
    payload = {
        "to_company_id": 2,
        "invite_message": "string"
    }
    response = await ac.post("/requests/", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json().get('detail') == "success"


# # my requests

async def test_my_requests_not_auth(ac: AsyncClient):
    response = await ac.get("/requests/my/")
    assert response.status_code == 403


async def test_my_requests_user_one(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/requests/my/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get('result')) == 0


async def test_my_requests_user_two(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/requests/my/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get('result')) == 1


async def test_my_requests_user_three(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test3@test.com']}",
    }
    response = await ac.get("/requests/my/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get('result')) == 1


# # company requests

async def test_company_requests_not_auth(ac: AsyncClient):
    response = await ac.get("/requests/companies/1/")
    assert response.status_code == 403


async def test_requests_company_not_found(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/requests/companies/100/", headers=headers)
    assert response.status_code == 404
    assert response.json().get('detail') == "This company not found"


async def test_requests_company_one_not_owner(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/requests/companies/1/", headers=headers)
    assert response.status_code == 403
    assert response.json().get('detail') == "it's not your company"


async def test_requests_company_one_success(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/requests/companies/1/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get('result')) == 2


# # request cancel


async def test_cancel_requests_not_auth(ac: AsyncClient):
    response = await ac.delete("/requests/5/")
    assert response.status_code == 403


async def test_cancel_requests_not_found(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.delete("/requests/12/", headers=headers)
    assert response.status_code == 404
    assert response.json().get('detail') == "Request not found"


async def test_cancel_requests_not_your(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test3@test.com']}",
    }
    response = await ac.delete("/requests/5/", headers=headers)
    assert response.status_code == 403
    assert response.json().get('detail') == "It is not your request"


async def test_cancel_request_success(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.delete("/requests/5/", headers=headers)
    assert response.status_code == 200
    assert response.json().get('detail') == "success"


# # accept request

async def test_accept_requests_not_auth(ac: AsyncClient):
    response = await ac.get("/requests/6/accept/")
    assert response.status_code == 403


async def test_accept_requests_not_found(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/requests/12/accept/", headers=headers)
    assert response.status_code == 404
    assert response.json().get('detail') == "Request not found"


async def test_accept_requests_not_owner(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/requests/6/accept/", headers=headers)
    assert response.status_code == 403
    assert response.json().get('detail') == "Only the owner of the company can accept requests"


# # decli request


async def test_decline_request_not_auth(ac: AsyncClient):
    response = await ac.get('/requests/7/decline/')
    assert response.status_code == 403
    assert response.json().get('detail') == "Not authenticated"


async def test_decline_request_not_found(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get('/requests/100/decline/', headers=headers)
    assert response.status_code == 404
    assert response.json().get('detail') == "Request not found"


async def test_decline_request_not_owner(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get('/requests/6/decline/', headers=headers)
    assert response.status_code == 403
    assert response.json().get('detail') == "Only the owner of the company can decline requests"


async def test_decline_request_success(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get('/requests/6/decline/', headers=headers)
    assert response.status_code == 200
    assert response.json().get('detail') == "success"


# #===============================


async def test_members_only_owner(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/companies/2/members/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get('result').get('users')) == 3


async def test_accept_requests(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/requests/7/accept/", headers=headers)
    assert response.status_code == 200


async def test_members_after_accept(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/companies/2/members/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get('result').get('users')) == 4


# # ===========

async def test_kick_member(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.delete("/companies/2/members/3/", headers=headers)
    assert response.status_code == 200


async def test_members_after_kick(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/companies/2/members/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get('result').get('users')) == 3


async def test_leave_member(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test4@test.com']}",
    }
    response = await ac.delete("/companies/2/leave/", headers=headers)
    assert response.status_code == 200


async def test_members_after_leave(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/companies/2/members/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get('result').get('users')) == 2


async def test_send_request_three_again_success(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test3@test.com']}",
    }
    payload = {
        "to_company_id": 2,
        "invite_message": "string"
    }
    response = await ac.post("/requests/", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json().get('detail') == "success"


async def test_accept_request_three(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/requests/8/accept/", headers=headers)
    assert response.status_code == 200


async def test_send_request_four_again_success(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test4@test.com']}",
    }
    payload = {
        "to_company_id": 2,
        "invite_message": "string"
    }
    response = await ac.post("/requests/", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json().get('detail') == "success"


async def test_accept_request_four(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/requests/9/accept/", headers=headers)
    assert response.status_code == 200
