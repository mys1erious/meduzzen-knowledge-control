# Meduzzen Internship - Knowledge Control App

## Deployed:
!!! (instance is deleted, doesnt work right now)
http://knowledge-control-api.mys1erious.com/docs

## Local:
**All commands should be executed from the project root**.

### Run the project:
- `docker compose up -d ` add `--build` for the first build

### Run the tests:
- `docker compose exec app pytest`

### Create migrations:
- `docker compose exec app makemigrations *migration_name*`

### Run migrations:
- `docker compose exec app migrate`

## Stack:
- Backend:
  - Python
  - FastAPI
  - Auth0/JWT
  - Postgresql
  - Redis
  - Docker Compose
  - Pytest
- Deployment AWS:
  - EC2, RDS, ElasticCache
