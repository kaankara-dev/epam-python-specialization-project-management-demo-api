from app.model.enums import ProjectRole
from app.repository.project import ProjectRepository
from app.schema.project import ProjectCreate, ProjectResponse, ProjectMemberAdd
from app.exception.project import (
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)


class ProjectService:
    def __init__(self, project_repo: ProjectRepository | None = None) -> None:
        self.project_repo = project_repo or ProjectRepository()

    def create_project(self, data: ProjectCreate, current_user_id: int) -> ProjectResponse:
        """Yeni proje oluşturur ve oluşturan kullanıcıyı otomatik OWNER yapar."""
        # 1. Projeyi oluştur (repo.create)
        project = self.project_repo.create(
            name=data.name,
            description=data.description,
            created_by_id=current_user_id,
        )

        # 2. Kullanıcıyı OWNER rolüyle üyeliğe ekle (repo.add_member)
        self.project_repo.add_member(
            project_id=project.id,
            user_id=current_user_id,
            role=ProjectRole.OWNER,
        )

        # 3. Pydantic ProjectResponse DTO'suna çevirip dön
        return ProjectResponse.model_validate(project)

    def add_member(
        self,
        project_id: int,
        member_data: ProjectMemberAdd,
        current_user_id: int
    ) -> None:
        """Sadece OWNER'ın projeye yeni üye eklemesine izin verir."""
        # 1. Proje var mı?
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        # 2. İşlemi yapan kullanıcının (current_user_id) yetkisini kontrol et
        actor_membership = self.project_repo.get_member(project_id=project_id, user_id=current_user_id)
        if not actor_membership:
            raise ProjectPermissionDeniedError(f"User {current_user_id} is not a member of this project")

        if actor_membership.role != ProjectRole.OWNER:
            raise ProjectPermissionDeniedError(f"User {current_user_id} has insufficient permissions")

        # 3. Yeni üyeyi kaydet
        self.project_repo.add_member(
            project_id=project_id,
            user_id=member_data.user_id,
            role=member_data.role,
        )

