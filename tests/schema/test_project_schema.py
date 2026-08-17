import pytest
from pydantic import ValidationError
from app.schema.project import ProjectCreate, ProjectUpdate, ProjectMemberAdd
from app.model.enums import ProjectRole


def test_project_create_valid():
    """Geçerli verilerle proje oluşturma şeması testi."""
    data = {"name": "EPAM Cloud Projesi", "description": "Örnek açıklama"}
    project = ProjectCreate(**data)
    assert project.name == "EPAM Cloud Projesi"
    assert project.description == "Örnek açıklama"


def test_project_create_name_too_short():
    """3 karakterden kısa isim verildiğinde ValidationError fırlatmalı."""
    with pytest.raises(ValidationError):
        ProjectCreate(name="AB")


def test_project_member_add_default_role():
    """Rol belirtilmediğinde varsayılan rolün PARTICIPANT olduğunu doğrula."""
    # Sadece user_id veriyoruz, role vermiyoruz:
    member_data = ProjectMemberAdd(user_id=1)

    assert member_data.user_id == 1
    assert member_data.role == ProjectRole.PARTICIPANT


def test_project_member_add_custom_role():
    """Özel rol belirtildiğinde o rolün atandığını doğrula."""
    member_data = ProjectMemberAdd(user_id=1, role=ProjectRole.OWNER)

    assert member_data.role == ProjectRole.OWNER