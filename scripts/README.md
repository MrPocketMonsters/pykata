# Scripts Directory

Helper scripts for publishing tasks. Run them from the repository root so imports resolve correctly.

## Table of Contents

- [Publish Kata (`publish_kata.py`)](#publish-kata-publish_katapy)
  - [Purpose](#purpose)
  - [Prerequisites](#prerequisites)
  - [Usage](#usage)
  - [Arguments](#arguments)
  - [What the script does](#what-the-script-does)
  - [Examples](#examples)
  - [Troubleshooting](#troubleshooting)
- [Seed Katas (`seed_katas.py`)](#seed-katas-seed_kataspy)
  - [Purpose](#purpose-1)
  - [Prerequisites](#prerequisites-1)
  - [Usage](#usage-1)
  - [Arguments](#arguments-1)
  - [What the script does](#what-the-script-does-1)
  - [Examples](#examples-1)
  - [Troubleshooting](#troubleshooting-1)
- [Package Lambda (`package_lambda.py`)](#package-lambda-package_lambdapy)
  - [Purpose](#purpose-2)
  - [Prerequisites](#prerequisites-2)
  - [Usage](#usage-2)
  - [Arguments](#arguments-2)
  - [What the script does](#what-the-script-does-2)
  - [Examples](#examples-2)
  - [Troubleshooting](#troubleshooting-2)

## Publish Kata (`publish_kata.py`)

### Purpose

Validates and publishes a kata: checks metadata, parses code, ensures the kata ID is unique, uploads the code to S3, and writes metadata to DynamoDB.

### Prerequisites

- Python virtual environment activated with project dependencies installed (see [Create and Activate a Virtualenv](../LOCAL_SETUP.md#2-create-and-activate-a-virtualenv)).
- AWS/localstack credentials and endpoints configured via environment variables (see [Create Your .env from the Template and Load It](../LOCAL_SETUP.md#4-create-your-env-from-the-template-and-load-it)).
- A kata directory containing both `metadata.json` and `main.py`.
  - `main.py`: The kata solution code. This file must be syntactically valid Python.
  - `metadata.json`: The kata metadata file. Must conform to the `KataMetadata` schema defined in `src/models/kata_metadata.py`.

    ```json
    {
      "id": "unique-kata-id",
      "title": "Kata Title",
      "description": "Detailed description of the kata.",
      "tags": ["tag1", "tag2"],
      "difficulty": "difficulty-level",
      "s3_key": "katas/unique-kata-id.py",
      "sample_input": "sample input for the kata",
      "sample_output": "expected output for the sample input"
    }
    ```

### Usage

From the repository root:

```bash
python -m scripts.publish_kata --directory PATH/TO/KATA_DIR [--update]
```

Running with `-m` ensures the `src` package is importable without manual `PYTHONPATH` edits.

### Arguments

- `--directory` (required): Path to the kata folder that includes `metadata.json` and `main.py`.
- `--update` (optional): If specified, allows updating an existing kata instead of creating a new one.

### What the script does

1. Validates the provided directory exists and contains `metadata.json` and `main.py`.
2. Loads and validates `metadata.json` against `KataMetadata` (fails fast on schema issues).
3. Parses `main.py` with `ast` to ensure syntactic correctness before publishing.
4. Checks DynamoDB to confirm the kata ID does or does not already exist, depending on whether `--update` is used.
5. Uploads `main.py` contents to S3 at the path specified by `s3_key` in metadata.
6. Creates the kata metadata record in DynamoDB.

### Examples

Publish a kata stored in `src/data/custom_dictionary`:

```bash
python -m scripts.publish_kata --directory src/data/custom_dictionary
```

Update a kata stored in `src/data/custom_dictionary`:

```bash
python -m scripts.publish_kata --directory src/data/custom_dictionary --update
```

### Troubleshooting

- **ModuleNotFoundError: No module named 'src'**: Run the script with `python -m scripts.publish_kata ...` from the repo root, or export the repo root to `PYTHONPATH` before running.
- **Metadata validation errors**: Ensure `metadata.json` matches the `KataMetadata` schema and includes required fields (`id`, `title`, `description`, `tags`, `difficulty`, `s3_key`, `sample_input`, `sample_output`).
- **AST parse errors**: Fix syntax errors in `main.py`; the script stops before uploading if parsing fails.

## Seed Katas (`seed_katas.py`)

### Purpose

Bulk-publishes all katas contained in a parent directory. Performs service health checks first, then calls the publish script once per kata directory.

### Prerequisites

- Same as `publish_kata.py`: active virtualenv with dependencies, configured AWS/localstack endpoints, and valid kata directories containing `metadata.json` and `main.py`.
- Local AWS services reachable (`check_health` for S3 and DynamoDB must succeed).

### Usage

From the repository root:

```bash
python -m scripts.seed_katas --directory PATH/TO/KATAS_PARENT [--update]
```

### Arguments

- `--directory` (required): Path to a folder whose immediate subdirectories each contain a kata (`metadata.json` + `main.py`).
- `--update` (optional): Forwarded to the publish script to update existing katas instead of creating new ones.

### What the script does

1. Validates the parent directory exists.
2. Runs S3 and DynamoDB health checks; aborts if either is unhealthy.
3. Enumerates subdirectories and prepares a publish command for each.
4. Executes `python -m scripts.publish_kata` per kata, adding `--update` when requested.
5. Collects exit codes and prints a success/failure summary.

### Examples

Seed all katas under `src/data`:

```bash
python -m scripts.seed_katas --directory src/data
```

Update all katas under `src/data`:

```bash
python -m scripts.seed_katas --directory src/data --update
```

### Troubleshooting

- **ModuleNotFoundError: No module named 'src'**: Run with `python -m scripts.seed_katas ...` from the repo root so package imports resolve.
- **Health check failures**: Ensure LocalStack/AWS endpoints are reachable and environment variables match your setup; the script exits before publishing if checks fail.
- **Partial failures**: The final summary lists which kata directories failed; rerun for those paths after fixing their metadata/code.

## Package Lambda (`package_lambda.py`)

> WARNING: This script is intended to be run on a Linux system, as AWS Lambda requires Linux-compatible binaries for dependencies. A lambda packaged on Windows or macOS may not work correctly when deployed to AWS Lambda.

### Purpose

Packages a Python AWS Lambda function by copying source files and dependencies into a build directory, then zipping it for deployment.

### Prerequisites

- Running on a Linux system (packaging for AWS Lambda requires Linux-compatible binaries).
- Python virtual environment activated with project dependencies installed (see [Create and Activate a Virtualenv](../LOCAL_SETUP.md#2-create-and-activate-a-virtualenv)).
- `pip` installed and accessible in the environment for installing dependencies.

### Usage

From the repository root:

```bash
python -m scripts.package_lambda [--directory PATH/TO/LAMBDA_DIR] [--build-directory PATH/TO/BUILD_DIR] [--output PATH/TO/OUTPUT_ZIP] [--requirements-file PATH/TO/REQUIREMENTS_FILE]
```

### Arguments

- `--directory` (optional): Path to the Lambda function directory containing source files. Defaults to `src`.
- `--build-directory` (optional): Temporary directory for building the package (default: `build`).
- `--output` (optional): Name of the output zip file (default: `terraform/lambda.zip`).
- `--requirements-file` (optional): Path to the `requirements.txt` file for dependencies (default: `requirements.txt`).

### What the script does

1. Validates the provided directory exists.
2. Creates a temporary build directory.
3. Copies all files from the specified directory to the build directory.
4. Installs dependencies listed in the specified `requirements.txt` into the build directory.
5. Creates a zip file from the contents of the build directory.
6. Cleans up the temporary build directory.

### Examples

Package a Lambda function in `src/lambda_function`:

```bash
python -m scripts.package_lambda --directory src/lambda_function
```

Package a Lambda function in `src/lambda_function` with a custom build directory, output zip name, and requirements file:

```bash
python -m scripts.package_lambda --directory src/lambda_function --build-directory build/my_lambda_build --output lambdas/my_lambda.zip --requirements-file src/lambda_function/requirements.txt
```

### Troubleshooting

- **ModuleNotFoundError: No module named 'src'**: Run the script with `python -m scripts.package_lambda ...` from the repo root, or export the repo root to `PYTHONPATH` before running.
- **Dependency installation failures**: Ensure the specified `requirements.txt` file exists and is correctly formatted. Check for network issues if dependencies fail to download.
