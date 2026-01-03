# GitHub Workflows Directory

Automated CI/CD pipelines for the PyKata project using GitHub Actions. These workflows ensure code quality, maintain test coverage, and validate infrastructure deployments.

## Table of Contents

- [Directory Structure](#directory-structure)
- [Continuous Integration (CI)](#continuous-integration-ci-ciyaml)
- [Deployment and E2E Testing](#deployment-and-e2e-testing-deploy-devyaml)
- [Local Simulation](#local-simulation)

## Directory Structure

```text
.github/workflows/
├── ci.yaml           # Main CI pipeline for code quality and testing
└── deploy-dev.yaml   # Deployment validation and E2E testing
```

## Continuous Integration (CI) (`ci.yaml`)

The primary quality gate for the repository. It runs on every pull request and push to the `master` branch to ensure that new changes do not break existing functionality or violate coding standards.

**Triggers:**

- `push` to `master`
- `pull_request` to `master`

**Key Steps:**

1. **Environment Setup**: Configures Python 3.12 and installs development dependencies from `requirements-dev.txt`.
2. **Linting & Formatting**: Executes `pre-commit` hooks to enforce code style and static analysis.
3. **Testing**: Runs unit and integration tests using `pytest`.
   - **Coverage Requirement**: The workflow fails if total coverage drops below **85%**.
4. **Coverage Reporting**: On successful pushes to `master`, it uploads coverage reports to Codecov for historical tracking.

## Deployment and E2E Testing (`deploy-dev.yaml`)

Validates the deployment process and performs full stack testing in an environment that mimics production using LocalStack.

**Triggers:**

- `pull_request` to `master` when **closed and merged**.

**Key Steps:**

1. **Infrastructure Mocking**: Starts LocalStack via Docker Compose to simulate AWS services (S3, DynamoDB, Lambda).
2. **Lambda Packaging**: Runs the `package_lambda.py` script to create the deployment artifact.
3. **Terraform Apply**: Initializes and applies the Terraform configuration for the `dev` environment against the LocalStack endpoint.
4. **E2E Validation**: Executes end-to-end tests (`pytest -m e2e`) to verify that the API, Lambda, and AWS services interact correctly.

## Local Simulation

Most steps performed by these workflows can be replicated locally for debugging purposes.

- To run CI checks locally, see [Step 11 in LOCAL_SETUP.md](../../LOCAL_SETUP.md#11-run-tests-and-hooks).
- To simulate the deployment pipeline, follow the full [Local Setup Guide](../../LOCAL_SETUP.md).
- For details on the test suites being executed, refer to the [Tests Directory Documentation](../../tests/README.md).
