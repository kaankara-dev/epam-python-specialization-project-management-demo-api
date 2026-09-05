from app.repository.document import DocumentRepository
from urllib.parse import unquote_plus

def handler(event: dict, context) -> dict:
    """
    AWS Lambda giriş noktası. S3 ObjectCreated event notification'ını işler,
    ilgili Document kaydının file_size_bytes alanını S3'ten raporlanan gerçek
    boyutla günceller.

    event şeması (gerçek AWS S3 notification formatı):
    {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "..."},
                    "object": {"key": "...", "size": 12345}
                }
            },
            ...
        ]
    }
    """
    document_repo = DocumentRepository()
    updated: list[int] = []
    not_found: list[str] = []

    for record in event["Records"]:
        record_key = unquote_plus(record["s3"]["object"]["key"])
        record_size = record["s3"]["object"]["size"]
        document = document_repo.get_by_s3_key(record_key)
        if document is not None:
            document_repo.update_file_size(document, record_size)
            updated.append(document.id)
        else:
            not_found.append(record_key)
    return {"updated": updated, "not_found": not_found}