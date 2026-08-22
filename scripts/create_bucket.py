import boto3
from app.core.config import get_settings

def create_local_bucket():
    settings = get_settings()
    s3 = boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        endpoint_url=settings.s3_endpoint_url,
    )
    try:
        s3.create_bucket(
            Bucket=settings.s3_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
        )
        print(f"✅ Bucket '{settings.s3_bucket_name}' MiniIO üzerinde başarıyla oluşturuldu!")
    except Exception as e:
        print(f"Bilgi / Hata: {e}")

if __name__ == "__main__":
    create_local_bucket()