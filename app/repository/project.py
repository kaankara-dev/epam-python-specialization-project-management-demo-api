from app.model.project import Project, ProjectMember
from app.model.enums import ProjectRole


class ProjectRepository:
    def create(self, name: str, created_by_id: int,  description: str | None = None) -> Project:
        """Yeni bir Project kaydı oluşturur ve döner."""
        return Project.create(
            name=name,
            description=description,
            created_by_id=created_by_id,
        )

    def get_by_id(self, project_id: int) -> Project | None:
        """ID'ye göre projeyi bulur, yoksa None döner."""
        return Project.get_or_none(Project.id==project_id)

    def add_member(
        self,
        project_id: int,
        user_id: int,
        role: ProjectRole = ProjectRole.PARTICIPANT
    ) -> ProjectMember:
        """Projeye yeni bir üye kaydı (ProjectMember) ekler."""
        return ProjectMember.create(project_id=project_id, user_id=user_id, role=role)

    def get_member(self, project_id: int, user_id: int) -> ProjectMember | None:
        """Kullanıcının projeye üye olup olmadığını ve rolünü bulur."""
        return ProjectMember.get_or_none(project_id=project_id, user_id=user_id)

    def delete(self, project_id: int) -> bool:
        """Projeyi siler; silindiyse True, proje bulunamadıysa False döner."""
        project = self.get_by_id(project_id)
        if not project:
            return False
        project.delete_instance()
        return True