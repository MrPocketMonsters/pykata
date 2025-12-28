"""Integration tests package.

Subdivided by environment:
- dev/: Tests against LocalStack with Terraform dev environment
- prod/: Tests against AWS production environment

All tests are automatically marked based on their directory location:
- tests/integration/dev/* → @pytest.mark.integration + @pytest.mark.dev_integration
- tests/integration/prod/* → @pytest.mark.integration + @pytest.mark.prod_integration
"""
