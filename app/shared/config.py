from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = (
        "postgresql+asyncpg://shopcloud:localdev@localhost:5432/shopcloud"
    )

    # Redis
    redis_url: str = "redis://localhost:6379"

    # AWS
    aws_region: str = "us-east-1"
    environment: str = "dev"

    # SQS (empty = disabled for local dev)
    sqs_queue_url: str = ""

    # S3
    s3_invoice_bucket: str = ""
    s3_static_bucket: str = ""
    cloudfront_domain: str = ""

    # Cognito (empty = auth bypass for local dev)
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_admin_pool_id: str = ""
    cognito_admin_client_id: str = ""
    cognito_region: str = "us-east-1"

    # CORS
    cors_origins: list[str] = ["*"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


def validate_prod() -> None:
    # Called from each service's startup hook. In prod, every AWS-backed
    # dependency must be real — no localhost, no empty SSM secrets — so a
    # misconfigured deploy fails fast instead of silently bypassing AWS.
    if settings.environment != "prod":
        return

    errors: list[str] = []
    required = {
        "DATABASE_URL": settings.database_url,
        "REDIS_URL": settings.redis_url,
        "S3_INVOICE_BUCKET": settings.s3_invoice_bucket,
        "SQS_QUEUE_URL": settings.sqs_queue_url,
        "COGNITO_USER_POOL_ID": settings.cognito_user_pool_id,
        "COGNITO_APP_CLIENT_ID": settings.cognito_app_client_id,
        "COGNITO_ADMIN_POOL_ID": settings.cognito_admin_pool_id,
        "COGNITO_ADMIN_CLIENT_ID": settings.cognito_admin_client_id,
    }
    for name, value in required.items():
        if not value:
            errors.append(f"{name} is empty")
        elif "localhost" in value or "127.0.0.1" in value:
            errors.append(f"{name} points to localhost in prod: {value}")

    if errors:
        raise RuntimeError(
            "Production config validation failed — refusing to start.\n  - "
            + "\n  - ".join(errors)
        )
