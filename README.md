# meduzzen-knowledge-control

**All commands should be executed from the project root**

### Run the project:
- `./scripts/start-dev.sh`

### Run the tests:
- `pytest`

### Run the project with tests in Docker:
- `docker build -t kc-app .` (done only once)
- `docker run -d --name kc-app -p 8000:8000 kc-app`

### Run the project with docker compose:
- `docker compose up -d`
