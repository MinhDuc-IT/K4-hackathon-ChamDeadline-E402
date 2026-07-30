# Skill: Deployment and DevOps

## 1. Purpose
This skill covers the strategies and best practices for moving the Discord bot and RAG system from a local development environment into a robust, scalable, and secure production environment.

## 2. Responsibilities
- Containerizing the application using Docker.
- Orchestrating multi-container setups (e.g., App + Vector DB) using Docker Compose.
- Configuring automated CI/CD pipelines (e.g., GitHub Actions).
- Deploying to cloud platforms like VPS, Railway, or Render.
- Managing production environment variables securely.
- Monitoring bot uptime and health.

## 3. When to use
- When the code is stable and ready to be hosted 24/7.
- When changing environment configurations or migrating servers.

## 4. When NOT to use
- During rapid local prototyping (running locally via `python main.py` is faster).

## 5. Workflow
1. **Dockerfile**: Create a lightweight Dockerfile (e.g., using `python:3.11-slim`), install dependencies, and define the startup command.
2. **Docker Compose**: (If applicable) Write a `docker-compose.yml` defining the bot service and any dependent services (like a Qdrant container).
3. **Secrets Management**: Setup secret variables in the host environment or deployment platform (Never commit `.env`).
4. **CI/CD setup**: Write a GitHub Actions workflow to build and deploy the container automatically upon push to the `main` branch.
5. **Deployment**: Push the code, monitor the build logs, and verify the bot comes online in Discord.

## 6. Best practices
- **Minimize Image Size**: Use `.dockerignore` to exclude local `venv`, `.git`, and raw data files. Use multi-stage builds if compiling dependencies.
- **Statelessness**: Ensure the bot container is stateless. Persistent data (like the Vector DB index or SQLite DB) must be mapped to a Docker Volume or hosted externally.
- **Health Checks**: Implement a simple HTTP health check endpoint or internal Discord ping task to ensure the bot hasn't frozen.

## 7. Coding conventions
- Use explicit version tags for base images (e.g., `python:3.11.4-slim` instead of `python:latest`).
- Structure the `docker-compose.yml` for clarity and explicitly define restart policies (e.g., `restart: always`).

## 8. Example prompts
- "Write a Dockerfile for our Discord bot that uses Python 3.11, installs requirements, and runs `src/main.py`."
- "Create a GitHub Actions workflow that runs pytest on Pull Requests and deploys to Railway on merge to main."

## 9. Example tasks
- "Set up a `docker-compose.yml` that spins up the Bot container and a local Qdrant Vector DB container."
- "Migrate the environment variables from a local `.env` file to Render's Secret Manager."

## 10. Common pitfalls
- **Hardcoded Secrets**: Accidentally copying `.env` into the Docker image.
- **Zombie Processes**: Not handling Docker stop signals properly, leading to abrupt database connection drops.
- **Volume Loss**: Running a local Vector DB in a container without a mounted volume, causing all data to be wiped on container restart.

## 11. Directory structure
```
.
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
└── .github/
    └── workflows/
        ├── test.yml
        └── deploy.yml
```

## 12. Suggested libraries
- `docker`
- `docker-compose`

## 13. References
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
