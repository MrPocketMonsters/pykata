# Terraform Environments

This directory contains environment-specific Terraform configurations that wrap the root infrastructure module with environment-appropriate settings. Each environment is an isolated workspace with its own state, variables, and provider configuration.

> **📚 See Also:**
>
> - [Terraform Root README](../README.md) — Infrastructure modules, variable reference, and architecture
> - [Modules README](../modules/README.md) — Individual resource module documentation

## Overview

Environments follow a **wrapper pattern** where each environment directory:

1. Defines environment-specific variables (LocalStack vs AWS, credentials, endpoints)
2. Calls the root module (`source = "../.."`) with those variables
3. Exposes root module outputs for consumption

This pattern allows the **same infrastructure code** (root module) to be deployed to different environments with different configurations.

```text
terraform/environments/<env>/
├── main.tf             # Wraps root module with env-specific variables
├── variables.tf        # Env-specific defaults (LocalStack, AWS creds, etc.)
├── outputs.tf          # Re-exports root module outputs
├── terraform.lock.hcl  # Provider lock file
└── tfplan              # Saved terraform plan file
```

## Architecture

```text
.env.example (source of truth)
    ↓ (TF_VAR_* after `source .env`)
environments/<env>/variables.tf (env defaults)
    ↓ (module "infra" { source = "../.." })
terraform/ (root module)
    ├── modules/dynamodb
    └── modules/s3
    ↓
AWS or LocalStack
```

## Available Environments

### dev/ (Development)

**Purpose**: Local development using LocalStack to emulate AWS services.

**Key Settings**:

- Provider: LocalStack endpoints (`http://localhost:4566`)
- Credentials: Test credentials (`test`/`test`)
- Endpoints: Custom LocalStack URLs for S3, DynamoDB, Lambda, API Gateway
- Provider flags: `s3_use_path_style=true`, skip validation/metadata checks
- S3 safety: `s3_force_destroy=true` (safe for dev cleanup)
- Billing: `PAY_PER_REQUEST` (on-demand)

**Resources Created**:

- DynamoDB table: `kata` (configurable)
- S3 bucket: `kata-code` (configurable)

---

### prod/ (Production) `planned`

**Purpose**: Production deployment to real AWS.

**Key Settings** (planned):

- Provider: Real AWS endpoints (default AWS SDK behavior)
- Credentials: AWS IAM credentials (via environment, IAM role, or AWS CLI profile)
- Endpoints: None (uses default AWS endpoints)
- Provider flags: All `false` (validates credentials, uses metadata API)
- S3 safety: `s3_force_destroy=false` (prevents accidental data loss)
- Versioning: `s3_versioning_enabled=true` (backup/rollback capability)
- Billing: Consider `PROVISIONED` with tuned RCUs/WCUs for cost optimization

**Resources Created** (planned):

- DynamoDB table: `kata` (configurable)
- S3 bucket: `kata-code` (configurable)

**Differences from Dev**:

| Setting | Dev | Prod |
| --- | --- | --- |
| Provider | LocalStack | AWS |
| Credentials | `test`/`test` | Real AWS creds |
| S3 Force Destroy | `true` | `false` |
| S3 Versioning | `false` | `true` |
| Validation Checks | Skipped | Enabled |
| Endpoints | LocalStack URLs | Default AWS |

> **Status:** Prod environment not yet implemented. See [Next Steps](#next-steps).

## Common Usage Patterns

### Standard Workflow

```bash
# 1. Load environment variables
set -a
source .env
set +a

# 2. Initialize (first time only or after module changes)
terraform -chdir=terraform/environments/<env> init

# 3. Review planned changes
terraform -chdir=terraform/environments/<env> plan -out=tfplan

# 4. Apply changes
terraform -chdir=terraform/environments/<env> apply "tfplan"

# 5. View outputs
terraform -chdir=terraform/environments/<env> output
```

### Using Workspaces for Parallel Work

Workspaces allow multiple isolated states within the same environment:

```bash
# Create a workspace for a feature branch
terraform -chdir=terraform/environments/dev workspace new feature-auth

# Switch between workspaces
terraform -chdir=terraform/environments/dev workspace select feature-auth
terraform -chdir=terraform/environments/dev workspace select default

# List all workspaces
terraform -chdir=terraform/environments/dev workspace list

# Each workspace has its own state
terraform -chdir=terraform/environments/dev apply
```

### Overriding Variables

> **📚 See:** [Terraform Root README - Overriding Variables](../README.md#overriding-variables) for detailed examples.

**Via `.env` file** (recommended):

```bash
set -a
source .env
set +a
terraform -chdir=terraform/environments/<env> plan -out=tfplan
```

**Via CLI**:

```bash
terraform -chdir=terraform/environments/<env> plan -out=tfplan \
  -var="dynamodb_table_name=custom-table"
```

## Environment Isolation

Each environment maintains **complete isolation**:

- **Separate state**: Each environment has its own `.terraform/` directory and state file
- **Separate credentials**: Dev uses test creds, prod uses real AWS creds
- **Separate resources**: No shared infrastructure between environments
- **Independent lifecycles**: Changes in dev don't affect prod

**State Files** (important):

- **Local state** (default): Stored in `<env>/.terraform/terraform.tfstate`
- **Remote state** (recommended for prod): Configure backend in `<env>/backend.tf` to use S3 + DynamoDB locking

## Best Practices

1. **Always run Terraform from environment directories**: Use `-chdir=terraform/environments/<env>` to ensure correct context
2. **Never commit state files**: Add `.terraform/` and `*.tfstate*` to `.gitignore`
3. **Use workspaces for feature branches**: Avoid state conflicts when multiple developers work on dev
4. **Review plans before apply**: Always run `plan` and review the diff before `apply`
5. **Use remote state for prod**: Avoid state file loss and enable team collaboration
6. **Separate AWS accounts for prod**: Use AWS Organizations to isolate prod from dev/staging
7. **Load `.env` consistently**: Always `source .env` before running Terraform to ensure consistent defaults

## Troubleshooting

**Common issues across environments:**

- **State locked**: `terraform -chdir=terraform/environments/<env> force-unlock <LOCK_ID>`
- **Provider authentication failed**: Check credentials are set correctly for the environment
- **Module not installed**: Run `terraform -chdir=terraform/environments/<env> init`
- **Resource already exists**: Either destroy and recreate, or import existing resource into state
- **lambda.zip not found**: Ensure the Lambda package is built and located at the expected path before applying Terraform.
- **Lambda dependency issues**: Ensure all dependencies are included in the Lambda package and compatible with AWS Lambda runtime.

> **📚 See:** [Package Lambda Script](../../scripts/README.md#package-lambda-package_lambdapy) for lambda packaging instructions and warnings.

**Environment-specific issues:**

- **Dev/LocalStack**: See [dev/README.md - Troubleshooting](dev/README.md#troubleshooting)
- **Prod/AWS**: Check AWS credentials, IAM permissions, and service quotas

> **📚 See:** [Terraform Root README - Troubleshooting](../README.md#troubleshooting) for detailed troubleshooting guides on initial development environment setup.

## Next Steps

- **Implement prod environment**: Create `prod/` directory with prod-safe defaults
- **Add remote state**: Configure S3 backend with DynamoDB locking for prod
- **CI/CD integration**: Automate `terraform plan` on PRs, `apply` on merge to main
- **Implement Lambda/API Gateway modules**: Expand infrastructure beyond DynamoDB and S3
