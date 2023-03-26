from httpx import AsyncClient


def get_base_quiz_payload():
    return {
        "name": "QUIZ1 COMPANY1",
        "description": "some_desc",
        "frequency": 10,
        "company_id": 1,
        "questions": [
            {
                "content": "QUIZ1 QUESTION1",
                "answers": [
                    {
                        "correct": True,
                        "content": "QUIZ1 QUESTION1 ANS1"
                    },
                    {
                        "correct": False,
                        "content": "QUIZ1 QUESTION1 ANS2"
                    }
                ]
            },
            {
                "content": "QUIZ1 QUESTION2",
                "answers": [
                    {
                        "correct": True,
                        "content": "QUIZ1 QUESTION2 ANS1"
                    },
                    {
                        "correct": False,
                        "content": "QUIZ1 QUESTION2 ANS2"
                    }
                ]
            }
        ]
    }


async def test_create_quiz_unauthorized(ac: AsyncClient):
    payload = get_base_quiz_payload()
    response = await ac.post("/quizzes/", json=payload)
    assert response.status_code == 403


async def test_bad_create_quiz__no_name(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = get_base_quiz_payload()
    payload['name'] = ''

    response = await ac.post("/quizzes/", json=payload, headers=headers)
    assert response.status_code == 422


async def test_bad_create_quiz__one_question(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = get_base_quiz_payload()
    payload['questions'].pop()

    response = await ac.post("/quizzes/", json=payload, headers=headers)
    assert response.status_code == 422


async def test_bad_create_quiz__one_answer(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = get_base_quiz_payload()
    payload['questions'][0]['answers'].pop()

    response = await ac.post("/quizzes/", json=payload, headers=headers)
    assert response.status_code == 422


async def test_bad_create_quiz__not_company_admin(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = get_base_quiz_payload()
    payload['company_id'] = 2

    response = await ac.post("/quizzes/", json=payload, headers=headers)
    assert response.status_code == 403


async def test_create_quiz_one_company_one(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }

    payload = get_base_quiz_payload()

    response = await ac.post("/quizzes/", json=payload, headers=headers)
    assert response.status_code == 201


async def test_create_quiz_two_company_one(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }

    payload = get_base_quiz_payload()
    payload['name'] = 'QUIZ2 COMPANY1'

    payload['questions'][0]['content'] = 'QUIZ2 QUESTION1'
    payload['questions'][0]['answers'][0]['content'] = 'QUIZ2 QUESTION1 ANS1'
    payload['questions'][0]['answers'][1]['content'] = 'QUIZ2 QUESTION1 ANS2'

    payload['questions'][1]['content'] = 'QUIZ2 QUESTION2'
    payload['questions'][1]['answers'][0]['content'] = 'QUIZ2 QUESTION2 ANS1'
    payload['questions'][1]['answers'][1]['content'] = 'QUIZ2 QUESTION2 ANS2'

    response = await ac.post("/quizzes/", json=payload, headers=headers)
    assert response.status_code == 201


async def test_create_quiz_one_company_two(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    payload = get_base_quiz_payload()
    payload['company_id'] = 2

    response = await ac.post("/quizzes/", json=payload, headers=headers)
    assert response.status_code == 201


async def test_get_all_quizzes(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/quizzes/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get("result").get('quizzes')) == 3


async def test_get_company_one_quizzes(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/companies/1/quizzes/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get("result").get('quizzes')) == 2


async def test_get_company_two_quizzes(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/companies/2/quizzes/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get("result").get('quizzes')) == 1


async def test_bad_get_quiz_by_id_not_found(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/quizzes/100/", headers=headers)
    assert response.status_code == 404


async def test_get_quiz_by_id_two(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/quizzes/2/", headers=headers)
    assert response.status_code == 200
    assert response.json().get("result").get("company_id") == 1
    assert response.json().get("result").get("name") == "QUIZ2 COMPANY1"
    assert response.json().get("result").get("description") == "some_desc"
    assert response.json().get("result").get("frequency") == 10

    questions = response.json().get("result").get("questions")
    assert len(questions) == 2

    assert questions[0]['content'] == 'QUIZ2 QUESTION1'
    answers1 = questions[0]['answers']
    assert len(answers1) == 2
    assert answers1[0]['content'] == 'QUIZ2 QUESTION1 ANS1'
    assert answers1[1]['content'] == 'QUIZ2 QUESTION1 ANS2'

    assert questions[1]['content'] == 'QUIZ2 QUESTION2'
    answers2 = questions[1]['answers']
    assert len(answers2) == 2
    assert answers2[0]['content'] == 'QUIZ2 QUESTION2 ANS1'
    assert answers2[1]['content'] == 'QUIZ2 QUESTION2 ANS2'


async def test_bad_update_quiz__unauthorized(ac: AsyncClient):
    payload = {
        "name": 'QUIZ1 COMPANY1 UPDATED',
        "description": "updated_desc",
        "frequency": 20
    }
    response = await ac.put("/quizzes/1/", json=payload)
    assert response.status_code == 403


async def test_bad_update_quiz__not_found(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "name": 'QUIZ1 COMPANY1 UPDATED',
        "description": "updated_desc",
        "frequency": 20
    }
    response = await ac.put("/quizzes/100/", json=payload, headers=headers)
    assert response.status_code == 404


async def test_bad_update_quiz__not_allowed(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "name": 'QUIZ1 COMPANY2 UPDATED',
        "description": "updated_desc",
        "frequency": 20
    }
    response = await ac.put("/quizzes/3/", json=payload, headers=headers)
    assert response.status_code == 403


async def test_update_quiz_one(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "name": 'QUIZ1 COMPANY1 UPDATED',
        "description": 'updated_desc',
        "frequency": 20
    }
    response = await ac.put("/quizzes/1/", json=payload, headers=headers)
    assert response.status_code == 200


async def test_get_quiz_one_by_id_updated(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/quizzes/1/", headers=headers)
    assert response.status_code == 200
    assert response.json().get("result").get("company_id") == 1
    assert response.json().get("result").get("name") == 'QUIZ1 COMPANY1 UPDATED'
    assert response.json().get("result").get("description") == 'updated_desc'
    assert response.json().get("result").get("frequency") == 20


async def test_update_quiz_one_question_one(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "content": "QUIZ1 QUESTION1 UPDATED"
    }
    response = await ac.put("/questions/1/", json=payload, headers=headers)
    assert response.status_code == 200


async def test_get_quiz_one_question_one_by_id_updated(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/questions/1/", headers=headers)
    assert response.status_code == 200
    assert response.json().get("result").get('content') == "QUIZ1 QUESTION1 UPDATED"


async def test_update_quiz_one_question_one_answer_one(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "content": "QUIZ1 QUESTION1 ANS1 UPDATED"
    }
    response = await ac.put("/answers/1/", json=payload, headers=headers)
    assert response.status_code == 200


async def test_get_quiz_one_question_one_answer_one_by_id_updated(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/answers/1/", headers=headers)
    assert response.status_code == 200
    assert response.json().get("result").get('content') == "QUIZ1 QUESTION1 ANS1 UPDATED"


async def test_add_quiz_one_question(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }

    payload = {
        "quiz_id": 1,
        "content": "QUIZ1 QUESTION3",
        "answers": [
            {
                "correct": True,
                "content": "QUIZ1 QUESTION3 ANS1"
            },
            {
                "correct": False,
                "content": "QUIZ1 QUESTION3 ANS2"
            }
        ]
    }

    response = await ac.post("/questions/", json=payload, headers=headers)
    assert response.status_code == 201


async def test_get_quiz_one_questions_by_id_updated(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/quizzes/1/questions/", headers=headers)
    assert response.status_code == 200

    questions = response.json().get("result")
    assert len(questions) == 3
    assert questions[2]['content'] == 'QUIZ1 QUESTION3'
    assert len(questions[2]['answers']) == 2


async def test_add_quiz_one_question_one_answer(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }

    payload = {
        "question_id": 1,
        "correct": False,
        "content": "QUIZ1 QUESTION1 ANS3"
    }

    response = await ac.post("/answers/", json=payload, headers=headers)
    assert response.status_code == 201


async def test_get_quiz_one_questions_answer_one_by_id_updated(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/questions/1/answers/", headers=headers)
    assert response.status_code == 200

    answers = response.json().get("result")
    assert len(answers) == 3
    assert answers[2]['content'] == 'QUIZ1 QUESTION1 ANS3'
    assert answers[2]['correct'] is False


async def test_get_quiz_one_by_id_full_updated(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/quizzes/1/", headers=headers)
    assert response.status_code == 200
    assert response.json().get("result").get("company_id") == 1
    assert response.json().get("result").get("name") == 'QUIZ1 COMPANY1 UPDATED'
    assert response.json().get("result").get("description") == 'updated_desc'
    assert response.json().get("result").get("frequency") == 20

    questions = response.json().get("result").get('questions')
    assert len(questions) == 3
    assert questions[0]['content'] == 'QUIZ1 QUESTION1 UPDATED'
    assert questions[1]['content'] == 'QUIZ1 QUESTION2'
    assert questions[2]['content'] == 'QUIZ1 QUESTION3'
    assert len(questions[2]['answers']) == 2

    answers1 = questions[0]['answers']
    assert len(answers1) == 3
    assert answers1[0]['content'] == 'QUIZ1 QUESTION1 ANS1 UPDATED'
    assert answers1[2]['content'] == 'QUIZ1 QUESTION1 ANS3'
    assert answers1[2]['correct'] is False


async def test_bad_delete_quiz_one__not_allowed(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.delete("/quizzes/1/", headers=headers)
    assert response.status_code == 403


async def test_delete_quiz_two_company_one(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.delete("/quizzes/2/", headers=headers)
    assert response.status_code == 204


async def test_get_all_quizzes_after_delete(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/quizzes/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get("result").get('quizzes')) == 2


async def test_get_company_one_quizzes_after_delete(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/companies/1/quizzes/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get("result").get('quizzes')) == 1


async def test_bad_get_quiz_two_question_one_after_delete(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/questions/3/", headers=headers)
    assert response.status_code == 404


async def test_bad_get_quiz_two_question_one_answer_one_after_delete(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/answers/5/", headers=headers)
    assert response.status_code == 404
