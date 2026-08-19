from app.model.document import Document


class DocumentRepository:
    def create(
        self,
        project_id: int,
        uploaded_by_id: int | None,
        file_name: str,
        s3_key: str,
        mime_type: str,
        file_size_bytes: int = 0,
    ) -> Document:
        """Yeni bir Document kaydı oluşturur."""
        return Document.create(
            project=project_id,
            uploaded_by=uploaded_by_id,
            file_name=file_name,
            s3_key=s3_key,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
        )

    def get_by_id(self, document_id: int) -> Document | None:
        """ID'ye göre dokümanı bulur."""
        return Document.get_or_none(Document.id == document_id)

    def list_by_project(self, project_id: int) -> list[Document]:
        """Bir projeye ait tüm dokümanları listeler."""
        return list(Document.select().where(Document.project == project_id))

    def delete(self, document_id: int) -> bool:
        """Doküman kaydını siler."""
        doc = self.get_by_id(document_id)
        if not doc:
            return False
        doc.delete_instance()
        return True