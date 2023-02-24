# meduzzen-knowledge-control

**All commands should be executed from the project root**

### Run the project:
- `./scripts/start-dev.sh`
- `docker compose up -d ` add `--build` for the first build

### Run the tests:
- `pytest`
- `docker compose exec app pytest`

### Run the project with tests in Docker:
- `docker build -t kc-app .` (done only once)
- `docker run -d --name kc-app -p 8000:8000 kc-app`
### Create migrations:
- `docker compose exec app makemigrations *migration_name*`

### Run the project with docker compose:
- `docker compose up -d`
### Run migrations:
- `docker compose exec app migrate`
