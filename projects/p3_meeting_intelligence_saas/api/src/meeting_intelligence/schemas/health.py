"""Health check and demonstration request/response schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness probe and version information response."""

    status: str = Field(description="Service status.", examples=["ok"])
    version: str = Field(description="Deployed API version.", examples=["0.1.0"])


class EchoRequest(BaseModel):
    """Input message payload for echo endpoint."""

    message: str = Field(
        min_length=1,
        description="Text to echo back.",
        examples=["Hello, meeting bot!"],
    )


class EchoResponse(BaseModel):
    """Echo endpoint response payload."""

    you_said: str = Field(description="The message that was sent.", examples=["Hello, meeting bot!"])
    length: int = Field(description="Character count of the message.", examples=[19])
