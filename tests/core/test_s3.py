import pytest
from moto import mock_aws
import boto3
from app.core.config import get_settings
from app.core.s3 import S3Client


@pytest.fixture
def s3_setup():
    """Moto ile RAM'de sanal bir S3 ortamı ve test bucket'ı oluşturur."""
    with mock_aws():
        settings = get_settings()
        # Mock S3 istemcisiyle bucket açıyoruz
        raw_s3 = boto3.client("s3", region_name=settings.aws_region)
        raw_s3.create_bucket(
            Bucket=settings.s3_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": settings.aws_region}
            if settings.aws_region != "us-east-1"
            else {},
        )
        yield S3Client()


def test_generate_presigned_upload_url(s3_setup):
    """Yükleme için oluşturulan Presigned URL doğru parametreleri içermelidir."""
    s3_client = s3_setup
    settings = get_settings()

    upload_url = s3_client.generate_presigned_upload_url(
        s3_key="projects/1/test.pdf",
        mime_type="application/pdf",
        expires_in=300
    )

    assert isinstance(upload_url, str)
    assert settings.s3_bucket_name in upload_url
    assert "projects/1/test.pdf" in upload_url
    assert "AWSAccessKeyId" in upload_url or "X-Amz-Signature" in upload_url


def test_generate_presigned_download_url(s3_setup):
    """İndirme için oluşturulan Presigned URL geçerli bir link üretmelidir."""
    s3_client = s3_setup
    settings = get_settings()

    download_url = s3_client.generate_presigned_download_url(
        s3_key="projects/1/test.pdf",
        expires_in=600
    )

    assert isinstance(download_url, str)
    assert settings.s3_bucket_name in download_url
    assert "projects/1/test.pdf" in download_url