"""This script seeds multiple katas from a specified directory into the repository by checking AWS services health and invoking the publish_kata script for each kata directory."""

import argparse
from os import path, listdir, system
from src.services.dynamo_service import check_health as check_dynamo_health
from src.services.s3_service import check_health as check_s3_health


def main():
    print("Starting kata seeding process...")

    # Set up argument parser with directory argument
    parser = argparse.ArgumentParser(description="Seed katas into the repository.")
    parser.add_argument(
        "--directory",
        type=str,
        required=True,
        help="The directory containing the kata directories seed.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        default=False,
        help="Set to True to update existing katas instead of creating new ones.",
    )
    args = parser.parse_args()


    # Validate that the provided directory exists
    if not path.isdir(args.directory):
        raise NotADirectoryError(f'The directory "{args.directory}" does not exist.')

    print(f'Successfully validated the existence of directory "{args.directory}".')


    # Check s3 and dynamo health
    print("Checking AWS services health...")
    if not check_s3_health():
        raise ConnectionError("S3 service is not healthy or bucket is inaccessible.")
    print("S3 service is healthy.")

    print("Checking DynamoDB service health...")
    if not check_dynamo_health():
        raise ConnectionError("DynamoDB service is not healthy or table is inaccessible.")
    print("DynamoDB service is healthy.")


    # Load directories inside the provided directory
    print(f'Preparing publish commands for katas in directory "{args.directory}"...')
    kata_dirs = [
        path.join(args.directory, d)
        for d in listdir(args.directory)
        if path.isdir(path.join(args.directory, d))
    ]

    # Iterate over each kata directory and execute the publish command
    line_command = lambda directory: f"python -m scripts.publish_kata --directory {directory}{' --update' if args.update else ''}"

    print("Publishing katas...")
    results = []
    success_count = 0
    failure_count = 0
    for kata_dir in kata_dirs:
        print(f" Running publish for kata directory: {kata_dir}...")
        result = system(line_command(kata_dir))
        results.append((kata_dir, result))
        if result == 0:
            success_count += 1
            print(f'  Successfully published kata from directory "{kata_dir}".')
        else:
            failure_count += 1
            print(f'  Failed to publish kata from directory "{kata_dir}".')

    # Print summary of results
    print(f"Kata seeding process completed with {success_count} successes and {failure_count} failures:")
    for kata_dir, result in results:
        status = "SUCCESS" if result == 0 else "FAILURE"
        print(f' - {kata_dir}: {status}')


if __name__ == "__main__":
    main()
