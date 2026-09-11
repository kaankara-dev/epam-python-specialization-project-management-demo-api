from fastapi import APIRouter, status

from app.lambda_handlers.document_size_handler import handler

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/s3-events", status_code=status.HTTP_200_OK)
def receive_s3_event(event: dict) -> dict:
    """
    MinIO (veya gerçek AWS S3) tarafından gönderilen ObjectCreated event
    notification'ını Lambda handler'a iletir.

    GÜVENLİK NOTU: Bu endpoint'te bilinçli olarak get_current_user gibi bir
    kullanıcı auth kontrolü YOK. Gerçek AWS'de S3 -> Lambda çağrısı zaten
    IAM resource-based policy ile sadece S3 servisine izin verilerek
    korunur; hiçbir zaman public bir HTTP endpoint olarak durmaz. Bizim
    yerel simülasyonumuzda bu korumanın karşılığı UYGULAMA KODUNDA değil,
    ALTYAPI SEVİYESİNDE olmalıdır: bu servis, docker-compose'da host'a port
    mapping edilmeden yalnızca container network'ü içinden (MinIO'nun
    webhook çağrısıyla) erişilebilir şekilde çalıştırılmalıdır. Production'a
    taşınırsa bu, VPC private subnet + security group kuralına karşılık
    gelir.

    TODO (üretim senaryosu, şu an kapsam dışı): docker-compose.yml'de app
    servisinin sadece internal network'te olduğunu, host'a port
    expose etmediğini doğrula.
    """
    return handler(event, None)