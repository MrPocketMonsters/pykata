# ⚙️ Local Setup Guide

Step-by-step instructions to get the project running locally on Windows (Git Bash/WSL or PowerShell) with LocalStack.

## 📋 Prerequisites

- Python 3.12 installed and on PATH
- Git installed
- Docker Desktop running (required for LocalStack)
- Terraform installed (v1.5+ recommended)

**Optional:**

- AWS CLI installed (for step 6 verification)

## 1) Clone and enter the repo

After this step, you will have a local copy of the repository and be inside its directory.

```bash
git clone https://github.com/MrPocketMonsters/pykata.git
cd pykata
```

## 2) Create and activate a virtualenv

After this step, you will have a Python virtual environment created and activated to isolate dependencies, ensuring they do not interfere with your global Python installation.

Git Bash / WSL:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

CMD:

```bat
python -m venv .venv
.\.venv\Scripts\activate.bat
```

## 3) Install dependencies

After this step, all required Python libraries for development and testing will be installed in your virtual environment (i.e. installed inside the project folder).

```bash
pip install -r requirements-dev.txt
pre-commit install
```

## 4) Create your .env from the template and load it

After this step, you will have a `.env` file with default environment variables for local development and a loaded environment for the current shell session.

- Create `.env` from template:

    ```bash
    cp .env.example .env
    # Edit .env only if you need non-default endpoints/ports
    ```

- Load `.env` variables into the shell with subprocess support:

    WSL/Git Bash:

    ```bash
    set -a
    source .env
    set +a
    ```

    CMD:

    ```cmd
    for /f "usebackq tokens=1,* delims== eol=#" %i in (".env") do @set "%i=%j"
    ```

    PowerShell:

    ```powershell
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#\s][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
        }
    }
    ```

## 5) Start LocalStack (Docker Compose)

After this step, LocalStack will be running locally in Docker containers, simulating AWS services for development and testing.

```bash
docker compose -f docker/docker-compose.yml up -d
```

- Wait until containers are healthy (check with `docker ps`)
- If you see port conflicts, stop other services using the 4566 port

## 6) (Optional) Verify LocalStack is reachable

After this step, you will confirm that LocalStack is running and accessible via AWS CLI commands. You may skip this step if AWS CLI is not installed or you prefer to verify connectivity via Terraform later.

```bash
aws --endpoint-url http://localhost:4566 dynamodb list-tables
aws --endpoint-url http://localhost:4566 s3 ls
```

## 7) Mock Infrastructure with Terraform

After this step, your terraform instance will download the necessary providers, create the tfstate file to track the infrastructure, and apply the configuration to create the mocked AWS resources in LocalStack.

- DynamoDB Table
- S3 Bucket
- IAM Role for Lambda
- CloudWatch Log Group for Lambda

```bash
terraform -chdir=terraform/environments/dev init
terraform -chdir=terraform/environments/dev apply -auto-approve
```

## 8) Run the FastAPI app locally

After this step, the FastAPI application will be running locally, allowing you to test and develop the API endpoints.

```bash
uvicorn src.api.main:app --reload --port 8000
```

- Swagger UI: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

## 9) Seed sample katas

After this step, sample katas will be published to the local DynamoDB and S3 emulated by LocalStack, allowing you to test the application with pre-loaded data.

Bulk seed katas in the `src/data` directory into LocalStack:

```bash
python -m scripts.seed_katas --directory src/data/
```

Or alternatively, seed a single kata.

```bash
python -m scripts.publish_kata --directory src/data/kata_to_publish/
```

In both cases, if you need to update an existing kata, add the `--update` flag.

> The `kata_to_publish` folder should contain `metadata.json` and `main.py` files. See [Scripts Directory Documentation](scripts/README.md) for more details.

## 10) Run tests and hooks

After this step, you will have verified that the codebase passes all pre-commit hooks and tests, ensuring code quality and correctness.

```bash
pre-commit run --all-files
pytest --cov=src --cov-report=term-missing
```

## ✅ Common troubleshooting

It this step, you will find solutions to common issues that may arise during setup and development.

- **Virtualenv not activating**: ensure you are running the correct shell command for your terminal.
- **Ports already in use (4566/8001)**: stop conflicting containers or processes, then re-run docker compose.
- **Terraform init/apply errors**:
  - Ensure LocalStack is running and healthy.
    > If the containers are healthy but errors persist, try restarting LocalStack: `docker compose -f docker/docker-compose.yml restart`.
  - Remove existing `terraform/environments/dev/terraform.tfstate` file and run `terraform apply` again.
    > Note you are not using -auto-approve here to inspect the infrastructure changes before applying.
- **AWS CLI missing**: install from <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html> or skip step 6.
- **Tests cannot find AWS endpoints**: check `.env` has `AWS_ENDPOINT_URL=http://localhost:4566` and app reload picks it up.
- **Kata publishing errors**: see [Scripts Directory Documentation](scripts/README.md) for troubleshooting kata publishing scripts.

## 🔮 Daily dev loop (cheat sheet)

1. Activate venv
2. `docker compose -f docker/docker-compose.yml up -d`
3. `terraform -chdir=terraform/environments/dev apply -auto-approve`
4. `uvicorn src.api.main:app --reload --port 8000`
5. Code → `pre-commit run --all-files` → `pytest` → push branch → open PR → let CI run
