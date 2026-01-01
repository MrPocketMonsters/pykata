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
