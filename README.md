# meduzzen-knowledge-control

### To run the project:
- write `./scripts/start-dev.sh` from the project root.

### To run the tests:
- write `pytest` from the project root.

### To run the project with tests in Docker:
- Write `docker build -t kc-app .` from the project root.
    <br>(Has to be done only once)
- Write `docker run -d --name kc-app -p 8000:8000 kc-app` from the project root.
