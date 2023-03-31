# meduzzen-knowledge-control
Dep

**All commands should be executed from the project root**.

### Run the project:
- `docker compose up -d ` add `--build` for the first build

### Run the tests:
- `docker compose exec app pytest`

### Create migrations:
- `docker compose exec app makemigrations *migration_name*`

### Run migrations:
- `docker compose exec app migrate`
