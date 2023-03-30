from httpx import AsyncClient


async def test_submit_attempt_unauthorized(ac: AsyncClient):
    payload = {
        "quiz_id": 1,
        "question_ids": [
            1, 2
        ],
        "answer_ids": [
            [1], [3]
        ]
    }
    response = await ac.post("/attempts/", json=payload)
    assert response.status_code == 403


async def test_bad_submit_attempt_not_member(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    payload = {
        "quiz_id": 1,
        "question_ids": [
            1, 2
        ],
        "answer_ids": [
            [1], [3]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 403


async def test_bad_submit_attempt_no_quiz_id(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "question_ids": [
            1, 2
        ],
        "answer_ids": [
            [1], [3]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 422


async def test_bad_submit_attempt_less_questions(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "quiz_id": 1,
        "question_ids": [
            1
        ],
        "answer_ids": [
            [1], [3]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 422


async def test_bad_submit_attempt_less_answers(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "quiz_id": 1,
        "question_ids": [
            1, 2
        ],
        "answer_ids": [
            [1]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 422


async def test_bad_submit_attempt_question_not_found(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "quiz_id": 1,
        "question_ids": [
            1, 100
        ],
        "answer_ids": [
            [1], [3]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 400


async def test_bad_submit_attempt_answer_not_found(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "quiz_id": 1,
        "question_ids": [
            1, 2
        ],
        "answer_ids": [
            [1], [100]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 400


async def test_bad_submit_attempt_answer_no_answer(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "quiz_id": 1,
        "question_ids": [
            1, 2
        ],
        "answer_ids": [
            [], [100]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 400


async def test_submit_attempt_one_quiz_one_score_100(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "quiz_id": 1,
        "question_ids": [
            1, 2
        ],
        "answer_ids": [
            [1], [3]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json().get('score') == 1.0


async def test_submit_attempt_two_quiz_one_score_100(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "quiz_id": 1,
        "question_ids": [
            1, 2
        ],
        "answer_ids": [
            [1], [3]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json().get('score') == 1.0


async def test_submit_attempt_three_quiz_one_score_50(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "quiz_id": 1,
        "question_ids": [
            1, 2
        ],
        "answer_ids": [
            [1], [4]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json().get('score') == 0.5


async def test_submit_attempt_four_quiz_three_score_100(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    payload = {
        "quiz_id": 3,
        "question_ids": [
            5, 6
        ],
        "answer_ids": [
            [9], [11]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json().get('score') == 1.0


async def test_submit_attempt_five_quiz_three_score_75(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    payload = {
        "quiz_id": 3,
        "question_ids": [
            5, 6
        ],
        "answer_ids": [
            [9, 10], [11]
        ]
    }
    response = await ac.post("/attempts/", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json().get('score') == 0.75


async def test_bad_get_company_avg_score__not_member(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/analytics/avg-score/?company_id=1", headers=headers)
    assert response.status_code == 403


async def test_bad_get_company_avg_score__forbidden(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/analytics/avg-score/?company_id=100", headers=headers)
    assert response.status_code == 403


async def test_get_company_one_avg_score(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/analytics/avg-score/?company_id=1", headers=headers)
    assert response.status_code == 200
    assert response.json().get('total_questions') == 6
    assert response.json().get('total_correct_answers') == 5
    assert response.json().get('avg_score') == 0.833


async def test_get_company_two_avg_score(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/analytics/avg-score/?company_id=2", headers=headers)
    assert response.status_code == 200
    assert response.json().get('total_questions') == 4
    assert response.json().get('total_correct_answers') == 3.5
    assert response.json().get('avg_score') == 0.875


async def test_bad_get_user_avg_score__not_found(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/analytics/avg-score/?user_id=100", headers=headers)
    assert response.status_code == 404


async def test_get_user_one_avg_score(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/analytics/avg-score/?user_id=1", headers=headers)
    assert response.status_code == 200
    assert response.json().get('total_questions') == 6
    assert response.json().get('total_correct_answers') == 5
    assert response.json().get('avg_score') == 0.833


async def test_get_user_two_avg_score(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/analytics/avg-score/?user_id=2", headers=headers)
    assert response.status_code == 200
    assert response.json().get('total_questions') == 4
    assert response.json().get('total_correct_answers') == 3.5
    assert response.json().get('avg_score') == 0.875


async def test_bad_get_quiz_avg_score__not_found(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/analytics/avg-score/?quiz_id=100", headers=headers)
    assert response.status_code == 404


async def test_get_quiz_one_avg_score(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/analytics/avg-score/?quiz_id=1", headers=headers)
    assert response.status_code == 200
    assert response.json().get('total_questions') == 6
    assert response.json().get('total_correct_answers') == 5
    assert response.json().get('avg_score') == 0.833


async def test_get_quiz_three_avg_score(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.get("/analytics/avg-score/?quiz_id=3", headers=headers)
    assert response.status_code == 200
    assert response.json().get('total_questions') == 4
    assert response.json().get('total_correct_answers') == 3.5
    assert response.json().get('avg_score') == 0.875


async def test_get_avg_score(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/analytics/avg-score/", headers=headers)
    assert response.status_code == 200
    assert response.json().get('total_questions') == 10
    assert response.json().get('total_correct_answers') == 8.5
    assert response.json().get('avg_score') == 0.85
