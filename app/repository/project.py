from datetime import datetime

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
        return ProjectMember.create(
            project=project_id,
            user=user_id,
            role=role,
        )

    def get_member(self, project_id: int, user_id: int) -> ProjectMember | None:
        return ProjectMember.get_or_none(project=project_id, user=user_id)


    def delete(self, project_id: int) -> bool:
        """Projeyi siler; silindiyse True, proje bulunamadıysa False döner."""
        project = self.get_by_id(project_id)
        if not project:
            return False
        project.delete_instance()
        return True


    def list_by_user(self, user_id: int) -> list[Project]:
        """Kullanıcının üyesi olduğu tüm projeleri döner."""
        return list(Project.select().join(ProjectMember).where(ProjectMember.user==user_id))


    def update(self, project_id: int, data: dict) -> Project | None:
        """Verilen alanları günceller; proje yoksa None döner."""
        project = self.get_by_id(project_id)
        if project is None:
            return None
        for key in data:
            project.__setattr__(key, data[key])
        project.updated_at = datetime.now()
        project.save()
        return project