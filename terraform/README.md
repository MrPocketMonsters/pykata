# Terraform Infrastructure

This directory contains the Infrastructure-as-Code (IaC) for the PyKata project using Terraform. The structure follows a root module pattern where the root defines reusable infrastructure, and environment-specific modules (e.g., `environments/dev`) provide environment-specific configuration and act as the entry points for Terraform operations.

## Directory Structure

```text
terraform/
├── main.tf                 # Root module: DynamoDB, S3, lambda IAM role and lambda function resource composition
├── variables.tf            # Root module: input variables (infrastructure + provider inputs)
├── outputs.tf              # Root module: outputs from composed resources
├── providers.tf            # AWS provider configuration (driven by root variables)
├── lambda.zip              # Packaged Lambda deployment artifact
├── modules/                # Reusable Terraform modules
│   ├── dynamodb/           # DynamoDB table module
│   └── s3/                 # S3 bucket module
└── environments/
    └── dev/                # Development environment (LocalStack)
        ├── main.tf         # Consumes root module with dev-specific values
        ├── variables.tf    # Dev-specific defaults (LocalStack, test creds)
        └── outputs.tf      # Exposes root outputs for dev
```

## Architecture & Design

### Separation of Concerns

- **Root module (`terraform/`)**: Defines reusable infrastructure resources and accepts provider configuration as inputs. Not environment-aware.
- **Environment modules (`terraform/environments/<env>/`)**: Wrap the root module and provide environment-specific defaults and configuration.
- **Modules (`terraform/modules/`)**: Reusable, self-contained resource definitions (DynamoDB, S3, etc.).

### Variable Flow

```text
.env.example (single source of truth)
    ↓ (TF_VAR_* environment variables after `source .env`)
terraform/environments/dev/variables.tf (dev defaults)
    ↓ (module "infra" { ... })
terraform/variables.tf (root infrastructure + provider inputs)
    ↓ (resources + provider "aws" { ... })
LocalStack or AWS
```

**Key Principle**: `.env.example` is the single source of truth for all default values. Dev environment overrides root defaults where needed (e.g., LocalStack endpoints, credentials).

### Provider Configuration Strategy

Provider settings (AWS credentials, endpoints, skip checks) are **not hardcoded in root**. Instead:

1. Dev environment defines provider-related variables with LocalStack-friendly defaults.
2. Dev passes these to root as `provider_*` prefixed inputs.
3. Root provider block uses these inputs, making root agnostic to dev/prod differences.

This allows the **same root module** to work with:

- **Dev**: LocalStack, test credentials, path-style S3, skip validation checks.
- **Prod**: Real AWS, real credentials, no skip checks, no custom endpoints.

## Usage

### Prerequisites

1. Terraform >= 1.0
2. AWS provider ~> 5.0
3. Python venv with dependencies (for `.env` sourcing)
4. LocalStack running (for dev): `docker-compose -f docker/docker-compose.yml up -d`

### Initialize & Plan (Dev)

```bash
# Load environment variables from .env (overrides all dev defaults)
source .env

# Initialize Terraform (downloads providers, modules)
terraform -chdir=terraform/environments/dev init

# Plan changes
terraform -chdir=terraform/environments/dev plan

# Apply changes
terraform -chdir=terraform/environments/dev apply
```

### Destroy (Dev)

```bash
terraform -chdir=terraform/environments/dev destroy
```

### Workspace Strategy (Optional)

For managing multiple dev/staging environments from the same code:

```bash
# Create a new workspace for a feature branch
terraform -chdir=terraform/environments/dev workspace new feature-x

# Switch between workspaces
terraform -chdir=terraform/environments/dev workspace select feature-x

# List workspaces
terraform -chdir=terraform/environments/dev workspace list
```

## Variable Reference

### Root Module Variables (`terraform/variables.tf`)

**Infrastructure Configuration**:

- `project_name` (string): Project name (default: `pykata`).
- `tags` (map(string)): Common tags for all resources (default: `{}`).

**DynamoDB**:

- `dynamodb_table_name` (string): DynamoDB table name (default: `kata`).
- `billing_mode` (string): Billing mode (`PAY_PER_REQUEST` or `PROVISIONED`, default: `PAY_PER_REQUEST`).
- `attribute_definitions` (list(object)): Additional attributes for indexes, each with `name` and `type` (S|N|B) (default: `[]`).
- `provisioned_read_capacity` (number): Read capacity units when `PROVISIONED` (default: `5`).
- `provisioned_write_capacity` (number): Write capacity units when `PROVISIONED` (default: `5`).

**S3**:

- `s3_bucket_name` (string): S3 bucket name (default: `kata-code`).
- `s3_versioning_enabled` (bool): Enable object versioning (default: `false`).
- `s3_force_destroy` (bool): Force destroy bucket even if not empty (default: `false`).
- `s3_acl` (string): Canned ACL (default: `private`). Valid: `private`, `public-read`, `public-read-write`, `authenticated-read`, `log-delivery-write`, `aws-exec-read`, `bucket-owner-read`, `bucket-owner-full-control`.

**Lambda**:

- `lambda_timeout` (number): Lambda timeout in seconds (default: `10`).
- `lambda_function_name` (string): Name of the Lambda function (default: `pykata_lambda_function`).
- `lambda_env_aws_endpoint` (string): API endpoint for requests inside the Lambda environment (no default; provided by environment).
- `lambda_env_aws_s3_endpoint` (string): S3 endpoint for requests inside the Lambda environment (no default; provided by environment).

**Provider Configuration (Inputs from Environment)**:

- `provider_environment` (string): Environment name (e.g., `dev`, `prod`).
- `provider_aws_access_key` (string, sensitive): AWS access key (no default; provided by environment).
- `provider_aws_secret_key` (string, sensitive): AWS secret key (no default; provided by environment).
- `provider_aws_region` (string): AWS region (no default; provided by environment).
- `provider_s3_use_path_style` (bool): Use path-style S3 (default: `false`). Set to `true` for LocalStack.
- `provider_skip_credentials_validation` (bool): Skip creds validation (default: `false`). Set to `true` for LocalStack.
- `provider_skip_metadata_api_check` (bool): Skip metadata API check (default: `false`). Set to `true` for LocalStack.
- `provider_skip_requesting_account_id` (bool): Skip requesting account ID (default: `false`). Set to `true` for LocalStack.
- `provider_aws_endpoints` (map(string)): Custom service endpoints (default: `{}`). For LocalStack, set S3, DynamoDB, Lambda, API Gateway endpoints.

### Dev Environment Variables (`terraform/environments/dev/variables.tf`)

All root variables are redeclared in dev with environment-specific defaults. Key differences:

- `s3_force_destroy` (default: `true`): Safe for dev; allows cleanup without data loss.
- `aws_access_key` (default: `test`): LocalStack test credential.
- `aws_secret_key` (default: `test`): LocalStack test credential.
- `aws_region` (default: `us-east-1`): Default region.
- `s3_use_path_style` (default: `true`): Required for LocalStack.
- `skip_credentials_validation` (default: `true`): LocalStack doesn't validate credentials.
- `skip_metadata_api_check` (default: `true`): LocalStack doesn't provide metadata API.
- `skip_requesting_account_id` (default: `true`): LocalStack doesn't implement account ID check.
- `aws_endpoints` (default: LocalStack URLs): Maps S3, DynamoDB, Lambda, API Gateway to LocalStack endpoints.

### Overriding Variables

**Via `.env` file**:

```bash
set -a
source .env
set +a
terraform -chdir=terraform/environments/dev plan
```

> **📚 See:** [Local Setup Documentation](../LOCAL_SETUP#4-create-your-env-from-the-template-and-load-it) for further details.

**Via CLI** (highest precedence):

```bash
terraform -chdir=terraform/environments/dev plan \
  -var="dynamodb_table_name=custom-table" \
  -var="s3_bucket_name=custom-bucket"
```

## Output Reference

### Root Outputs (`terraform/outputs.tf`)

- `region`: AWS region being used.
- `project_name`: Project name.
- `dynamodb_table_name`: Name of the created DynamoDB table.
- `dynamodb_table_arn`: ARN of the created DynamoDB table.
- `s3_bucket_name`: Name of the created S3 bucket.
- `s3_bucket_arn`: ARN of the created S3 bucket.
- `lambda_role_arn`: IAM Role ARN for Lambda.
- `lambda_function_arn`: ARN of the created Lambda function.
- `lambda_function_name`: Name of the created Lambda function.

### Accessing Outputs

After `terraform apply`, view outputs:

```bash
terraform -chdir=terraform/environments/dev output

# Single output:
terraform -chdir=terraform/environments/dev output dynamodb_table_name

# JSON format:
terraform -chdir=terraform/environments/dev output -json
```

### Dev Outputs (`terraform/environments/dev/outputs.tf`)

Dev re-exports root outputs for convenience. When working in dev, you can reference the same output names as the root.

## The Lambda Deployment Package

The Lambda function deployment package (`lambda.zip`) is pre-packaged and included in the Terraform root directory. It contains the necessary code and dependencies for the Lambda function. Instructions on how to build or update this package can be found in the [Lambda Packaging Documentation](../scripts/README.md#package-lambda-package_lambdapy).

## Troubleshooting

### Terraform Initialization Error

```text
Error: Failed to install provider
```

**Solution**: Ensure internet connectivity and valid Terraform version.

```bash
terraform -chdir=terraform/environments/dev init -upgrade
```

### LocalStack Endpoint Unreachable

```text
Error: error putting S3 Bucket [...]: NotConnected
```

**Solution**: Ensure LocalStack is running and endpoints are correct.

```bash
docker-compose -f docker/docker-compose.yml up -d

# Verify endpoints:
echo $LOCALSTACK_ENDPOINT        # Should be http://localhost:4566
echo $LOCALSTACK_S3_ENDPOINT     # Should be http://s3.localhost.localstack.cloud:4566
```

### AWS Credentials Rejected

```text
Error: error validating provider credentials: error calling STS GetCallerIdentity
```

**Solution**: For dev (LocalStack), this is normal. Ensure `skip_credentials_validation` is `true` in dev config.

```bash
terraform -chdir=terraform/environments/dev plan -var="skip_credentials_validation=true"
```

### State Lock Issues

If Terraform state is locked (e.g., after a crashed apply):

```bash
terraform -chdir=terraform/environments/dev force-unlock <LOCK_ID>
```

## Best Practices

1. **Always use `.env`**: Load environment variables before running Terraform to ensure consistent defaults.
2. **Use workspaces for parallel work**: Create a workspace per feature branch to avoid state conflicts.
3. **Review plans before apply**: Always run `plan` and review the output before `apply`.
4. **Commit state files carefully**: `.tfstate` files should never be committed to version control; use remote state (e.g., S3 backend) in production.
5. **Use `-target` sparingly**: Avoid targeting specific resources unless necessary; it can break dependencies.
6. **Validate regularly**: Run `terraform validate` to catch configuration errors early.

## Next Steps

- **Prod environment**: Create `terraform/environments/prod/` with prod-safe defaults (no `force_destroy`, versioning enabled, real AWS credentials).
- **Lambda module**: Implement `modules/lambda/` for Lambda function configuration.
- **API Gateway module**: Implement `modules/api_gateway/` for REST API setup.
- **IAM module**: Implement `modules/iam/` for roles and policies.
- **Remote state**: Move state to S3 backend with locking (DynamoDB) for team collaboration.

## References

- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [LocalStack Documentation](https://docs.localstack.cloud/)
