import boto3
from botocore.config import Config
from app.core.config import get_settings


class S3Client:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket_name = settings.s3_bucket_name

        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url,
            config=Config(signature_version="s3v4"),
        )

    def get_signed_url(
        self,
        method: str,
        s3_key: str,
        params: dict | None = None,
        expires_in: int = 300,
    ) -> str:
        base_params = {"Bucket": self.bucket_name, "Key": s3_key}
        if params:
            base_params.update(params)

        return self.client.generate_presigned_url(
            ClientMethod=method,
            Params=base_params,
            ExpiresIn=expires_in,
        )

    def generate_presigned_upload_url(
        self,
        s3_key: str,
        mime_type: str,
        expires_in: int = 300,
    ) -> str:
        return self.get_signed_url(
            "put_object",
            s3_key,
            params={"ContentType": mime_type},
            expires_in=expires_in,
        )

    def generate_presigned_download_url(
        self,
        s3_key: str,
        expires_in: int = 300,
    ) -> str:
        return self.get_signed_url(
            "get_object",
            s3_key,
            expires_in=expires_in,
        )