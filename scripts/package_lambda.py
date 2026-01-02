"""Script to package AWS Lambda functions into deployment-ready zip files."""

import argparse
import os
import time
import shutil
import zipfile


class PathNotFoundError(ValueError):
    """Custom exception for invalid paths."""

class EmptyDirectoryError(ValueError):
    """Custom exception for empty directories."""


def _walk_with_exclude(
        base_path: str,
        exclude_relpaths: list[str] = ["__pycache__"]
):
    """Recursively yield files from the base path, excluding specified relative paths.

    Args:
        base_path (Path): The base directory to start searching from.
        exclude_relpaths (list[str], optional): List of relative paths to exclude. Defaults to ["__pycache__"].

    Yields:
        str: Full path to each file found.
    """

    # Validate base path
    if not os.path.exists(base_path):
        raise PathNotFoundError(f"The path '{base_path}' does not exist.")

    # If base path is a file, yield it directly
    if os.path.isfile(base_path):
        yield base_path
        return

    # Else, iterate through directory contents
    items = list(os.listdir(base_path))
    if not items:
        raise EmptyDirectoryError(f"The directory '{base_path}' is empty.")

    for item in items:
        if item in exclude_relpaths:
            continue

        next_path = f"{base_path}/{item}"
        try:
            yield from _walk_with_exclude(next_path, exclude_relpaths)
        except EmptyDirectoryError:
            continue


def main():
    print("Starting AWS Lambda packaging process...")

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Package AWS Lambda functions into zip files.")
    parser.add_argument(
        "--directory",
        type=str,
        default="src",
        help="Directory containing Lambda function folders to be packaged.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="lambda.zip",
        help="Output zip file name (default: lambda.zip).",
    )
    parser.add_argument(
        "--requirements-file",
        type=str,
        default="requirements.txt",
        help="Path to the requirements.txt file for dependencies (default: requirements.txt).",
    )
    args = parser.parse_args()


    # Validate that the provided directory exists
    if not os.path.isdir(args.directory):
        raise ValueError(f"The provided source directory '{args.directory}' is not a valid directory.")

    print(f"Packaging Lambda functions from directory: {args.directory}...")


    # Create a temporary build directory
    build_path = "build"
    print(f"Creating build directory {build_path}...")

    if os.path.exists(build_path):
        print(f"Removing existing build directory {build_path}...")
        shutil.rmtree(build_path)

    os.makedirs(build_path, exist_ok=True)

    print(f"Build directory {build_path} is ready.")


    # Copy files to build directory, excluding specified paths (__pycache__ by default)
    print("Copying files to build directory...")

    for next_path in _walk_with_exclude(args.directory):
        os.makedirs(os.path.dirname(f"{build_path}/{next_path}"), exist_ok=True)
        shutil.copy2(next_path, f"{build_path}/{next_path}")
        print(f"Copied: {next_path}")

    print("All files copied to build directory.")


    # Install dependencies.
    print("Installing dependencies...")
    requirements_path = args.requirements_file
    if not os.path.isfile(requirements_path):
        print(f"No requirements file found at {requirements_path}. Skipping dependency installation.")
    else:
        output = os.system(f"pip install -r {requirements_path} -t {build_path}")
        if output != 0:
            raise RuntimeError("Failed to install dependencies.")


    # Create zip file from build directory
    print(f"Creating deployment zip file {args.output}...")

    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(build_path):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, build_path)
                zipf.write(full_path, relative_path)


    # Clean up build directory
    print(f"Removing build directory {build_path}...")

    for i in range(3):
        try:
            shutil.rmtree(build_path)
            print("Build directory removed successfully.")
            break
        except Exception as e:
            print(f"Attempt {i+1} to remove build directory failed: {e}")
            time.sleep(2)


    print(f"Deployment zip file '{args.output}' created successfully.")

if __name__ == "__main__":
    main()
