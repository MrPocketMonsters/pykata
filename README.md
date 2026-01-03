# 🥋 PyKata CI/CD Showcase

**[Specialization] DevOps External course LatAm November 2025**

[![ci](https://github.com/MrPocketMonsters/pykata/actions/workflows/ci.yaml/badge.svg)](https://github.com/MrPocketMonsters/pykata/actions/workflows/ci.yaml)
[![deploy-dev](https://github.com/MrPocketMonsters/pykata/actions/workflows/deploy-dev.yaml/badge.svg)](https://github.com/MrPocketMonsters/pykata/actions/workflows/deploy-dev.yaml)
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

**Current Status:**

- Pre-commit, Pytest, and GitHub Actions CI/CD pipelines are fully implemented.
- Docker Compose with LocalStack enables local development and testing.
- Terraform modules for DynamoDB and S3 are complete; API Gateway and Lambda modules are pending.
- Pydantic models and service layers for DynamoDB, S3, and code execution are implemented and tested.
- Backend FastAPI endpoints for health check, kata listing, kata detail, and code execution are implemented and tested.
- Publish and seed kata scripts are available for managing kata data.
- Packaging script for Lambda deployment is implemented.
- Lambda deployment via Terraform has started, with a basic deployed Lambda function for health check.

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
  - `GET /katas/{id}` returning kata metadata plus `.py` code from S3
  - `POST /katas/run` fetching the kata `.py` from S3, executing it in a constrained subprocess with user input, and returning stdout/stderr.
- **Data layer:**
  - S3 bucket storing each kata as a single `main.py` file
  - DynamoDB table storing kata metadata (id, title, description, tags, s3_key, sample input/output)
- **Frontend:**
  - Kata list and detail views
  - Read-only code viewer
  - Run form to submit custom input and display execution output
- **Local development** will mirror the cloud stack using LocalStack and Docker Compose.

Execution safety measures will be enforced: kata code will run in dedicated lambda execution with a strict timeout and no network access. Inputs will be size-limited, and failures will return captured stderr to the caller. As of now, the execution sandbox is a simple subprocess with timeout in the local development server.

## 📁 Repository Layout

```text
.
├─ src/
│  ├─ api/                  # FastAPI app for local dev (parity with Lambda handlers)
│  ├─ lambdas/              # Lambda entrypoints
│  ├─ models/               # Pydantic/dataclass models
│  ├─ services/             # Kata loader, runner, s3/dynamo clients
│  └─ data/                 # Seed katas metadata (json)
├─ frontend/                # React + Vite app
├─ terraform/
│  ├─ modules/              # api_gateway, lambda, dynamodb, s3, iam
│  ├─ environments/         # dev (LocalStack), prod
├─ .github/workflows/       # CI (lint/test) and CD (deploy) pipelines
├─ docker/                  # Dockerfiles and compose for local stack
├─ scripts/                 # Helper scripts (publish kata, package lambda)
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ e2e/
├─ requirements.txt         # Production dependencies
├─ requirements-dev.txt     # Development dependencies
├─ pyproject.toml           # Black, isort, mypy configuration
├─ .pre-commit-config.yaml  # Pre-commit hooks configuration
├─ pytest.ini               # Pytest configuration
├─ .coveragerc              # Coverage.py configuration
├─ .editorconfig            # Editor configuration
├─ .env.example             # Environment variables template
├─ LOCAL_SETUP.md           # Local development setup instructions
├─ RETROSPECTIVE.md         # Sprint retrospective with personal insights
└─ README.md
```

## 💻 Local Development

Once set up, the local development workflow will be:

For extensive instructions, see [LOCAL_SETUP.md](LOCAL_SETUP.md).

- Create and activate a Python virtual environment (venv):

  ```bash
  python -m venv .venv
  source .venv/bin/activate
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

- Load environment variables:

  ```bash
  set -a
  source .env
  set +a
  ```

- Start LocalStack and services via Docker Compose:

  ```bash
  docker compose -f docker/docker-compose.yml up -d
  ```

- Initialize infrastructure with Terraform in the dev environment:

  ```bash
  terraform -chdir=terraform/environments/dev init
  terraform -chdir=terraform/environments/dev apply -auto-approve
  ```

- Run FastAPI locally for rapid iteration:

  ```bash
  uvicorn src.api.main:app --reload --port 8000
  ```

- Store seed katas in `src/data`.

  Publish all seed katas with:

  ```bash
  scripts/seed_katas.py --directory src/data
  ```

  or publish a single kata with:

  ```bash
  scripts/publish_kata.py --directory src/data/kata_dir
  ```

  Use the `--update` flag to update existing katas in both scripts.

- Execute tests with `pytest`; pre-commit hooks will enforce style and typing (black, flake8, mypy).
- Create short-lived feature branches, develop, run `pre-commit run --all-files`, run `pytest`, open a PR, and let CI validate before merge.

## 🚀 CI/CD Workflows

The pipelines will be implemented as follows:

- **On pull request:** checkout code, install dependencies, run linting (black/flake8), type-checking (mypy), and tests (pytest with coverage), then report results.
- **On merge to main (Sprint 1):** build and package the backend; apply Terraform to deploy the Lambda and minimal supporting infrastructure to a dev environment (LocalStack or AWS dev).
- **On merge to main (Sprint 2):** additionally build the frontend and sync to S3 (with CloudFront invalidation if configured).
- **Branching strategy:** short-lived feature branches, PR required; all status checks must pass before merge is allowed.

## ✅ Getting Started

### Sprint 1 (Weeks 1-2): Foundation & Backend

#### Phase 1: Project Foundation ✔️

- Repository structure, pre-commit hooks, and quality tools configured
- CI pipeline established with GitHub Actions (linting, type-checking, testing, coverage)
- LocalStack + Docker Compose for local development environment

#### Phase 2: Infrastructure as Code ✔️

- Terraform modules for DynamoDB (kata metadata), S3 (kata code), and IAM roles
- Local dev environment configuration pointing to LocalStack
- Infrastructure initialization scripts

#### Phase 3: Backend Development ✔️

- Pydantic models for kata metadata and execution results
- Service layers: DynamoDB client, S3 client, secure code execution sandbox
- FastAPI endpoints: `/health`, `/katas`, `/katas/{id}`, `POST /katas/{id}/run`
- Request logging and error handling middleware

#### Phase 4: Testing & Quality Gates ✔️

- Unit tests with pytest and coverage tracking (target ≥85%)
- Sample kata data for validation
- Execution service tests with timeout and sandbox constraints

#### Phase 5: CI/CD Deployment ✔️

- Lambda handler packaging with dependencies
- Deployment workflow for dev environment
- Artifact management and versioning

### Sprint 2 (Weeks 3-4): Frontend & Production

#### Phase 1: Frontend Development

- React + Vite scaffold with component architecture
- Kata list, detail, and code viewer components
- Execution form with real-time result display

#### Phase 2: Advanced Infrastructure

- Lambda integration with API Gateway
- Production-ready Terraform modules (API Gateway, CloudWatch, CloudFront)
- Multi-environment setup (dev with LocalStack, prod with AWS)

#### Phase 3: Integration & Observability

- End-to-end integration tests
- CloudWatch monitoring and alarms
- Performance and security testing

#### Phase 4: Production Hardening

- CORS, rate limiting, and input validation
- Security policies and documentation
- S3 static frontend deployment

#### Phase 5: Release & Documentation

- API documentation with cURL examples
- Deployment runbooks and troubleshooting guides
- Release notes and version tagging

## 📊 Sprint 1 Progress

| Task | Story Points | Status | Notes |
| --- | --- | --- | --- |
| 1.1 - Repository Setup | 5 | ✅ Complete | pre-commit, pyproject.toml, requirements configured |
| 1.2 - LocalStack & Docker | 3 | ✅ Complete | docker-compose with LocalStack + DynamoDB Admin |
| 1.3 - GitHub Actions CI | 5 | ✅ Complete | CI workflow, badges, Codecov integration |
| 1.4 - Terraform Infrastructure | 8 | ✅ Complete | DynamoDB & S3 modules completed |
| 1.5 - Models & Services | 8 | ✅ Complete | Pydantic models and service layers in development |
| 1.6 - FastAPI Endpoints | 8 | ✅ Complete | Ready to start |
| 1.7 - Seed Data | 3 | ✅ Complete | Depends on FastAPI & Terraform (1.4, 1.6) |
| 1.8 - Tests (85% coverage) | 8 | ✅ Complete | Basic test structure, targeting 85%+ coverage |
| 1.9 - CI/CD Deployment | 5 | ✅ Complete | Depends on FastAPI endpoints (1.6) |
| 1.10 - Documentation | 3 | ✅ Complete | API docs, LOCAL_SETUP, troubleshooting |

**Sprint 1 Completion:** 100% (10 of 10 tasks complete | 0 in progress | 0 blocked)

### Implementation Highlights

Key implementation points and measurable artifacts produced by the project.

- **Quality & Tooling:** Pre-commit and test tooling enforce style and correctness (black, flake8, mypy, pytest).
- **Local Development:** Docker Compose spins up LocalStack (S3, DynamoDB, Lambda emulation) for fast local iteration.
- **Infrastructure as Code:** Terraform modules provide repeatable infra provisioning with LocalStack support for local dev and cloud-ready modules for production.
- **Services Implemented:**
  - DynamoDB client for kata metadata CRUD
  - S3 client for kata code storage and retrieval
  - Execution service running kata code in a constrained subprocess with timeout
- **API Surface:** FastAPI endpoints for health (`GET /health`), listing (`GET /katas`), detail (`GET /katas/{id}`) and execution (`POST /katas/run`) with centralized logging and error middleware.
- **Helper Scripts:**
  - Kata publishing and seeding scripts to populate S3 and DynamoDB
  - Lambda packaging script to bundle code and dependencies for deployment
- **Testing Metrics:**
  - Unit tests: 116
  - Integration tests: 18
  - End-to-end tests: 8
  - Coverage: ~95% (CI enforces ≥85%)
- **CI/CD:** GitHub Actions workflows for PR checks (lint, type-check, tests) and a deployment pipeline for dev environment.
- **Documentation:** 12 Markdown files for extensive documentation (References, Guides, Troubleshooting).

## 🏆 Milestones

- **Sprint 1 Deliverable:** Deployed backend to a dev environment with health and kata listing/execution available. ✔️
- **Sprint 2 Deliverable:** Frontend available via S3/CloudFront and full CI/CD in place for backend and frontend.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
