"""Models for Kata metadata and execution results."""

from pydantic import BaseModel


class KataMetadata(BaseModel):
    """Metadata model for a coding kata, representing a table in DynamoDB."""

    id: str
    """Unique identifier for the kata."""
    title: str
    """Title of the kata."""
    description: str
    """Detailed description of the kata."""
    tags: list[str]  # "arrays", "strings"
    """Tags associated with the kata."""
    difficulty: str  # "beginner", "intermediate", "advanced"
    """Difficulty level of the kata."""
    s3_key: str
    """S3 key where the kata code is stored."""
    sample_input: str
    """Sample input for the kata."""
    sample_output: str
    """Expected output for the sample input."""


class KataExecution(BaseModel):
    """Model for executing a kata."""

    kata_id: str
    """Identifier of the kata to be executed."""
    user_input: str
    """Input provided by the user for execution."""
    max_timeout: int = 10
    """Maximum execution time in seconds."""


class ExecutionResult(BaseModel):
    """Result model for the execution of a kata."""

    success: bool
    """Indicates if the kata execution was successful."""
    stdout: str
    """Standard output from the kata execution."""
    execution_time_ms: int
    """Execution time in milliseconds."""
