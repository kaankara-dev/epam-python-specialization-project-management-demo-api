from uuid import uuid4
from app.core.s3 import S3Client
from app.model.project import Project
from app.repository.project import ProjectRepository
from app.repository.document import DocumentRepository
from app.schema.document import DocumentCreateRequest, DocumentUploadResponse, DocumentResponse
from app.exception.project import ProjectNotFoundError, ProjectPermissionDeniedError
from app.exception.document import DocumentNotFoundError


class DocumentService:
    def __init__(
        self,
        project_repo: ProjectRepository | None = None,
        document_repo: DocumentRepository | None = None,
        s3_client: S3Client | None = None,
    ) -> None:
        self.project_repo = project_repo or ProjectRepository()
        self.document_repo = document_repo or DocumentRepository()
        self.s3_client = s3_client or S3Client()

    def request_upload(
        self,
        project_id: int,
        request_data: DocumentCreateRequest,
        current_user_id: int,
    ) -> DocumentUploadResponse:
        """Kullanıcının projeye dosya yükleme iznini kontrol eder ve Presigned Upload URL döner."""
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        member = self.project_repo.get_member(project_id=project_id, user_id=current_user_id)
        if not member:
            raise ProjectPermissionDeniedError(f"User {current_user_id} is not a member of project {project_id}")

        s3_key = f"projects/{project_id}/{uuid4().hex}_{request_data.file_name}"

        upload_url = self.s3_client.generate_presigned_upload_url(
            s3_key=s3_key,
            mime_type=request_data.mime_type,
        )

        doc = self.document_repo.create(
            project_id=project_id,
            uploaded_by_id=current_user_id,
            file_name=request_data.file_name,
            s3_key=s3_key,
            mime_type=request_data.mime_type,
        )

        return DocumentUploadResponse(
            document_id=doc.id,
            upload_url=upload_url,
            s3_key=s3_key,
        )

    def get_download_url(
        self,
        document_id: int,
        current_user_id: int,
    ) -> DocumentResponse:
        """Doküman indirme yetkisini kontrol eder ve Presigned Download URL döner."""
        document = self.document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")
        membership = self.project_repo.get_member(
            project_id=document.project.id,
            user_id=current_user_id,
        )
        if membership is None:
            raise ProjectPermissionDeniedError(
                f"User {current_user_id} is not a member of project {document.project.id}")

        s3_key = document.s3_key
        signed_download_url = self.s3_client.generate_presigned_download_url(
            s3_key=s3_key)

        return DocumentResponse(id=document_id,
                                project_id=document.project.id,
                                uploaded_by_id=document.uploaded_by.id if document.uploaded_by else None,
                                file_name=document.file_name,
                                file_size_bytes= document.file_size_bytes,
                                mime_type=document.mime_type,
                                download_url=signed_download_url,
                                created_at=document.created_at)