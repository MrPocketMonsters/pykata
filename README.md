# 🥋 PyKata CI/CD Showcase

**[Specialization] DevOps External course LatAm November 2025**

[![CI](https://github.com/MrPocketMonsters/pykata/actions/workflows/ci.yaml/badge.svg)](https://github.com/MrPocketMonsters/pykata/actions/workflows/ci.yaml/badge.svg)
[![codecov](https://codecov.io/gh/MrPocketMonsters/pykata/branch/master/graph/badge.svg)](https://codecov.io/gh/MrPocketMonsters/pykata)

A deliberately small but complete exercise to showcase CI/CD craftsmanship around a serverless-friendly Python application. The domain is intentionally simple: an expository catalog of coding katas, each shipped with a single Python solution file. Anonymous users can browse the kata list, read the code, and execute it by providing custom input. The true goal is to demonstrate disciplined pipelines, infrastructure-as-code, and short-lived feature branch workflows.

## 🧭 Table of Contents

- [Program Context](#-program-context)
- [Outcome](#-outcome)
- [Tech Stack](#️-tech-stack)
- [Architecture](#️-architecture)
- [Repository Layout](#-repository-layout)
- [Local Development](#-local-development)
- [CI/CD Workflows](#-cicd-workflows)
- [Getting Started](#-getting-started)
- [Milestones](#-milestones)

## 📚 Program Context

This project is part of the **[Specialization] DevOps External course LatAm November 2025**, which focuses on EngX practices and CI/CD. PyKata is the Python module exercise that demonstrates these concepts in a practical, end-to-end deliverable: a complete CI/CD pipeline for a serverless application deployed to AWS.

The learning goals are:

- Master short-lived feature branch workflows and GitHub pull request processes
- Understand Lambda functions and serverless architecture on AWS
- Practice infrastructure-as-code with Terraform
- Build automated testing and quality gates in GitHub Actions
- Deploy applications with zero-downtime and rollback capability

## 🏁 Outcome

By the end of this exercise, the repository will contain:

- A fully functional backend (FastAPI for local development, AWS Lambda for production) exposing three endpoints: kata listing, detail, and execution.
- A simple frontend (React/Vite) that allows users to browse katas, view code, and execute solutions with custom input.
- Automated pipelines enforcing code quality: linting (black, flake8), type-checking (mypy), and unit tests (pytest) on every pull request.
- Infrastructure-as-code (Terraform) for both local (LocalStack) and cloud (AWS) deployments.
- A working example of short-lived feature branches, PR-based validation, and automated deployment on merge to main.

## 🛠️ Tech Stack

- Language: Python 3.12, TypeScript (frontend)
- Backend: FastAPI (local dev), AWS Lambda + API Gateway (prod)
- Frontend: React + Vite
- Infra as Code: Terraform
- Local cloud emulation: LocalStack (S3, DynamoDB, Lambda, API Gateway)
- CI/CD: GitHub Actions (pre-commit, lint, type-check, tests, build, deploy)
- Packaging: Docker for local orchestration; zip for Lambda artifacts
- Quality gates: black, flake8, mypy, pytest + coverage

## 🏗️ Architecture

The planned architecture will consist of:

- **API Gateway and Lambda functions** fronting three endpoints:
  - `GET /katas` returning kata metadata from DynamoDB
  - `GET /katas/{id}` returning kata metadata plus a reference to its code in S3
  - `POST /katas/{id}/run` fetching the kata `.py` from S3, executing it in a constrained subprocess with user input, and returning stdout/stderr
- **Data layer:**
  - S3 bucket storing each kata as a single `main.py` file
  - DynamoDB table storing kata metadata (id, title, description, tags, s3_key, sample input/output)
- **Frontend:**
  - Kata list and detail views
  - Read-only code viewer
  - Run form to submit custom input and display execution output
- **Local development** will mirror the cloud stack using LocalStack and Docker Compose.

Execution safety measures will be enforced: kata code will run in a subprocess with a strict timeout and no network access. Inputs will be size-limited, and failures will return captured stderr to the caller.

## 📁 Repository Layout

```text
.
├─ src/
│  ├─ api/                 # FastAPI app for local dev (parity with Lambda handlers)
│  ├─ lambdas/             # Lambda entrypoints
│  ├─ models/              # Pydantic/dataclass models
│  ├─ services/            # Kata loader, runner, s3/dynamo clients
│  └─ data/                # Seed katas metadata (json)
├─ frontend/               # React + Vite app
├─ terraform/
│  ├─ modules/             # api_gateway, lambda, dynamodb, s3, iam
│  ├─ environments/        # dev (LocalStack), prod
├─ .github/workflows/      # CI (lint/test) and CD (deploy) pipelines
├─ docker/                 # Dockerfiles and compose for local stack
├─ scripts/                # Helper scripts (publish kata, package lambda)
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ e2e/
├─ requirements.txt
├─ requirements-dev.txt
├─ pyproject.toml
├─ .env.example
└─ README.md
```

## 💻 Local Development

Once set up, the local development workflow will be:

- Create and activate a Python virtual environment (venv):

  ```bash
  python -m venv .venv
  source .venv/Scripts/activate  # Git Bash/WSL
  # or .venv\Scripts\Activate.ps1 (PowerShell)
  # or .venv\Scripts\activate.bat (CMD)
  ```

- Install dependencies and pre-commit hooks:

  ```bash
  pip install -r requirements-dev.txt
  pre-commit install
  ```

- Copy environment variables template and configure:

  ```bash
  cp .env.example .env
  # Edit .env if needed (defaults work for local development)
  ```

- Start LocalStack and services via Docker Compose:

  ```bash
  docker compose -f docker/docker-compose.yml up -d
  ```

- Run FastAPI locally for rapid iteration:

  ```bash
  uvicorn src.api.main:app --reload --port 8000
  ```

- Store seed katas in `src/data`; use `publish_kata.py` to push kata code and metadata to S3/Dynamo (LocalStack in dev).
- Execute tests with `pytest`; pre-commit hooks will enforce style and typing (black, flake8, mypy).
- Create short-lived feature branches, develop, run `pre-commit run --all-files`, run `pytest`, open a PR, and let CI validate before merge.

## 🚀 CI/CD Workflows

The pipelines will be implemented as follows:

- **On pull request:** checkout code, install dependencies, run linting (black/flake8), type-checking (mypy), and tests (pytest with coverage), then report results.
- **On merge to main (Sprint 1):** build and package the backend; apply Terraform to deploy the Lambda and minimal supporting infrastructure to a dev environment (LocalStack or AWS dev).
- **On merge to main (Sprint 2):** additionally build the frontend and sync to S3 (with CloudFront invalidation if configured).
- **Branching strategy:** short-lived feature branches, PR required; all status checks must pass before merge is allowed.

## ✅ Getting Started

**Sprint 1 (Weeks 1-2):** Foundation and backend

1. Setup repository structure, pre-commit hooks, and GitHub Actions CI pipeline
2. Configure LocalStack and Docker Compose for local development
3. Build the FastAPI backend with kata listing, detail, and execution endpoints
4. Implement the execution service with sandbox constraints
5. Write unit and integration tests (target 70%+ coverage)
6. Provision minimal dev infrastructure and deploy the backend (health + `GET /katas`) using Terraform

**Sprint 2 (Weeks 3-4):** Frontend and deployment

1. Set up React/Vite frontend scaffold
2. Build kata list and detail views
3. Implement the code viewer and execution form
4. Configure Terraform modules for Lambda, API Gateway, DynamoDB, and S3
5. Build CD pipeline: automate backend and frontend deployment on merge to main

See the backlog for detailed issue breakdown and progress tracking.

## 🏆 Milestones

- **Sprint 1 Deliverable:** Deployed backend to a dev environment with health and kata listing available.
- **Sprint 2 Deliverable:** Frontend available via S3/CloudFront and full CI/CD in place for backend and frontend.
