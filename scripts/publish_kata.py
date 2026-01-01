"""This script publishes a kata to the repository by uploading its code to S3 and creating its metadata entry in DynamoDB."""

import argparse
from os import path
import json
import ast

from src.models.kata import KataMetadata
from src.services.dynamo_service import (
    ItemNotFoundError,
    get_kata,
    create_kata,
)
from src.services.s3_service import upload_kata_code


def main():
    print("Starting kata publication process...")

    # Set up argument parser with directory argument
    parser = argparse.ArgumentParser(description="Publish a kata to the repository.")
    parser.add_argument(
        "--directory",
        type=str,
        required=True,
        help="The directory containing the kata files to publish.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        default=False,
        help="Set to True to update an existing kata instead of creating a new one.",
    )
    args = parser.parse_args()

    if args.update:
        print("Update mode enabled: existing kata will be replaced if it exists.")

    # Validate that the provided directory exists
    if not path.isdir(args.directory):
        raise NotADirectoryError(f'The directory "{args.directory}" does not exist.')


    # Validate both metadata.json and main.py exist in the directory
    metadata_path = path.join(args.directory, "metadata.json")
    if not path.isfile(metadata_path):
        raise FileNotFoundError(f'"metadata.json" not found in directory "{args.directory}".')

    main_path = path.join(args.directory, "main.py")
    if not path.isfile(main_path):
        raise FileNotFoundError(f'"main.py" not found in directory "{args.directory}".')


    # Load metadata
    try:
        metadata = json.load(open(metadata_path, "r", encoding="utf-8"))
        metadata = KataMetadata(**metadata)
    except Exception as e:
        raise ValueError(f"Failed to load or validate metadata.json: {e}")

    print(f'Kata "{metadata.title}" (ID: {metadata.id}) metadata validated successfully.')

    # Load main.py content
    try:
        with open(main_path, "r", encoding="utf-8") as f:
            main_content = f.read()
        ast.parse(main_content)
    except Exception as e:
        raise ValueError(f"Failed to load or parse main.py: {e}")

    print(f'main.py in directory "{args.directory}" parsed successfully.')


    # Validate that the kata does not already exist in DynamoDB
    print(f'Checking if kata with ID "{metadata.id}" already exists in the repository...')
    try:
        get_kata(metadata.id)
        if not args.update:
            raise ValueError(f'Kata with ID "{metadata.id}" already exists in the repository.')
    except ItemNotFoundError:
        if args.update:
            raise RuntimeError(f'Kata with ID "{metadata.id}" does not exist. Cannot update non-existing kata.')
    except Exception as e:
        raise RuntimeError(f"Failed to check existing kata in DynamoDB: {e}")


    # Publish the kata
    print(f'Kata "{metadata.title}" (ID: {metadata.id}) is ready to be published.')

    # Upload kata code to S3
    print("Uploading kata code to S3...")
    try:
        upload_kata_code(metadata.id, metadata.s3_key, main_content)
    except Exception as e:
        raise RuntimeError(f"Failed to upload kata code to S3: {e}")
    print("Kata code uploaded to S3 successfully.")

    # Create kata entry in DynamoDB
    print("Creating kata entry in DynamoDB...")
    try:
        create_kata(metadata)
    except Exception as e:
        raise RuntimeError(f"Failed to create kata entry in DynamoDB: {e}")
    print("Kata entry created in DynamoDB successfully.")

    print(f'Kata "{metadata.title}" (ID: {metadata.id}) published successfully.')

if __name__ == "__main__":
    main()
