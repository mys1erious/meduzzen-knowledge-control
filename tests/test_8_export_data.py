import json
from _csv import reader
from io import StringIO
from httpx import AsyncClient


async def test_bad_export_my_results_unauthorized(ac: AsyncClient):
    response = await ac.get("/export/my-results/")
    assert response.status_code == 403


async def test_export_user1_results_json(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    filename = 'fn1'

    response = await ac.get(f"/export/my-results/?format=json&filename={filename}", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["content-disposition"] == f'attachment; filename="{filename}"'

    results = json.loads(response.content.decode())
    for res in results:
        assert res['user_id'] == 1


async def test_export_user1_results_csv(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    filename = 'fn1'

    response = await ac.get(f"/export/my-results/?format=csv&filename={filename}", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == 'text/csv; charset=utf-8'
    assert response.headers["content-disposition"] == f'attachment; filename="{filename}"'

    csv_data = StringIO(response.content.decode())
    csv_reader = reader(csv_data)
    rows = list(csv_reader)

    assert rows[0] == ['quiz_id', 'user_id', 'company_id', 'question_id', 'answer_id', 'correct']
    for i in range(1, len(rows)):
        assert rows[i][1] == '1'


async def test_export_user2_results_json(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    filename = 'fn1'

    response = await ac.get(f"/export/my-results/?format=json&filename={filename}", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["content-disposition"] == f'attachment; filename="{filename}"'
    results = json.loads(response.content.decode())
    for res in results:
        assert res['user_id'] == 2


async def test_export_user2_results_csv(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    filename = 'fn1'

    response = await ac.get(f"/export/my-results/?format=csv&filename={filename}", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == 'text/csv; charset=utf-8'
    assert response.headers["content-disposition"] == f'attachment; filename="{filename}"'

    csv_data = StringIO(response.content.decode())
    csv_reader = reader(csv_data)
    rows = list(csv_reader)
    assert rows[0] == ['quiz_id', 'user_id', 'company_id', 'question_id', 'answer_id', 'correct']
    for i in range(1, len(rows)):
        assert rows[i][1] == '2'


async def test_bad_export_company_one_results_unauthorized(ac: AsyncClient):
    response = await ac.get("/export/company-results/1/")
    assert response.status_code == 403


async def test_bad_export_company_one_results_not_admin(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }

    response = await ac.get("/export/company-results/1/", headers=headers)
    assert response.status_code == 403


async def test_bad_export_company_one_results_company_doesnt_exist(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }

    response = await ac.get("/export/company-results/100/", headers=headers)
    assert response.status_code == 403


async def test_bad_export_company_one_results_user_doesnt_exist(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }

    response = await ac.get("/export/company-results/1/?user_id=100", headers=headers)
    assert response.status_code == 403


async def test_bad_export_company_one_user_two_forbidden(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }

    response = await ac.get("/export/company-results/1/?user_id=2", headers=headers)
    assert response.status_code == 403


async def test_export_company_one_results_all(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }

    response = await ac.get("/export/company-results/1/?filename=fn1", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["content-disposition"] == 'attachment; filename="fn1"'

    results = json.loads(response.content.decode())
    for res in results:
        assert res['company_id'] == 1


async def test_export_company_one_results_user_one(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }

    response = await ac.get("/export/company-results/1/?filename=fn1&user_id=1", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["content-disposition"] == 'attachment; filename="fn1"'

    results = json.loads(response.content.decode())
    for res in results:
        assert res['company_id'] == 1
        assert res['user_id'] == 1


async def test_export_company_two_results_all(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }

    response = await ac.get("/export/company-results/2/?filename=fn1", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["content-disposition"] == 'attachment; filename="fn1"'

    results = json.loads(response.content.decode())
    for res in results:
        assert res['company_id'] == 2


async def test_export_company_two_results_user_two(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }

    response = await ac.get("/export/company-results/2/?filename=fn1&user_id=2", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["content-disposition"] == 'attachment; filename="fn1"'

    results = json.loads(response.content.decode())
    for res in results:
        assert res['company_id'] == 2
        assert res['user_id'] == 2


async def test_bad_export_quiz_one_results_unauthorized(ac: AsyncClient):
    response = await ac.get("/export/quiz-results/1/")
    assert response.status_code == 403


async def test_bad_export_quiz_one_results_not_admin(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }

    response = await ac.get("/export/quiz-results/1/", headers=headers)
    assert response.status_code == 403


async def test_bad_export_quiz_doesnt_exist(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }

    response = await ac.get("/export/quiz-results/100/", headers=headers)
    assert response.status_code == 404


async def test_export_quiz_one_results(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }

    response = await ac.get("/export/quiz-results/1/?filename=fn1", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["content-disposition"] == 'attachment; filename="fn1"'

    results = json.loads(response.content.decode())
    for res in results:
        assert res['quiz_id'] == 1


async def test_export_quiz_three_results(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }

    response = await ac.get("/export/quiz-results/3/?filename=fn1", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["content-disposition"] == 'attachment; filename="fn1"'

    results = json.loads(response.content.decode())
    for res in results:
        assert res['quiz_id'] == 3
