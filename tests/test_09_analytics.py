from httpx import AsyncClient


async def test_get_my_last_attempts_unauthorized(ac: AsyncClient):
    response = await ac.get("analytics/my-last-attempts/")
    assert response.status_code == 403


async def test_get_my_last_attempts(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("analytics/my-last-attempts/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['quiz_id'] == 1


async def test_get_my_general_avg_score(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("analytics/avg-score/?user_id=1", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        'user_id': 1,
        'total_questions': 6,
        'total_correct_answers': 5.0,
        'avg_score': 0.833
    }


async def test_my_user_avg_scores_by_time(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("analytics/avg-scores-by-time/?user_id=1", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data[0]['quiz_id'] == 1

    result1 = data[0]['result']
    assert result1[0]['avg_score'] == 1
    assert result1[1]['avg_score'] == 1
    assert result1[2]['avg_score'] == 0.833


async def test_get_members_avg_scores_by_time(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("analytics/members-avg-scores-by-time/?company_id=1", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data[0]['user_id'] == 1

    result1 = data[0]['result']
    assert result1[0]['avg_score'] == 1
    assert result1[1]['avg_score'] == 1
    assert result1[2]['avg_score'] == 0.833


async def test_get_members_last_attempt(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("analytics/members-last-attempt/?company_id=1", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['user_id'] == 1
