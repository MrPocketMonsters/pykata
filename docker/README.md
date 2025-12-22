# 🐋 Docker Directory

This directory contains the Docker Compose setup for local development and testing of the PyKata project using LocalStack to emulate AWS services and DynamoDBAdmin for managing DynamoDB instances.

## Services

- **localstack**: This service runs LocalStack, which emulates AWS services such as S3, DynamoDB, Lambda, and API Gateway.
- **dynamodb-admin**: This service runs DynamoDBAdmin, a web-based interface for managing DynamoDB instances. It connects to the LocalStack DynamoDB endpoint.

## Usage

1. Ensure you have Docker and Docker Compose installed on your machine (both contained in Docker Desktop).
2. Load environment variables from the `.env` file in the project root (see `LOCAL_SETUP.md` for instructions).
3. Navigate to this directory in your terminal.
4. Run the following command to start the services:

   ```bash
   docker-compose up -d
   ```

   alternatively, run from the project root with:

   ```bash
    docker-compose -f docker/docker-compose.yml up -d
    ```

5. Access DynamoDBAdmin at `http://localhost:8001` to manage your DynamoDB tables.

## Throubleshooting

- If you encounter issues with LocalStack not starting correctly, ensure that the required ports are available and not blocked by other services.
  This ports are used:
  - LocalStack: `4566` (edge port for all services)
  - DynamoDBAdmin: `8001` (web interface)
- Check the logs of the LocalStack container for any error messages:

  ```bash
  docker logs pykata-localstack
  ```

- If you cannot access DynamoDBAdmin, ensure that the pykata-network (or docker_pykata-network) network is created and both services are connected to it.

  ```bash
  docker network ls
  docker network inspect pykata-network
  # docker network inspect docker_pykata-network
  ```
