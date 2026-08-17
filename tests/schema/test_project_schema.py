import pytest
from pydantic import ValidationError
from app.schema.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectMemberAdd,
    ProjectResponse,
)
from app.model.enums import ProjectRole
from datetime import datetime, timezone


# ==========================================
# 1. ProjectCreate Testleri & Edge Case'ler
# ==========================================

def test_project_create_valid():
    """Geçerli isim ve açıklama ile şema başarıyla doğrulanmalı."""
    data = {"name": "EPAM Cloud Projesi", "description": "Detaylı açıklama"}
    schema = ProjectCreate(**data)
    assert schema.name == "EPAM Cloud Projesi"
    assert schema.description == "Detaylı açıklama"


def test_project_create_without_description():
    """Açıklama verilmediğinde varsayılan olarak None olmalı."""
    schema = ProjectCreate(name="Minimal Proje")
    assert schema.name == "Minimal Proje"
    assert schema.description is None


@pytest.mark.parametrize("invalid_name", ["", "AB", "a" * 151])
def test_project_create_name_boundary_violations(invalid_name):
    """İsim 3 karakterden kısa veya 150 karakterden uzun olamaz."""
    with pytest.raises(ValidationError):
        ProjectCreate(name=invalid_name)


def test_project_create_description_too_long():
    """Açıklama 1000 karakterden uzun olamaz."""
    with pytest.raises(ValidationError):
        ProjectCreate(name="Geçerli İsim", description="A" * 1001)


# ==========================================
# 2. ProjectUpdate Testleri & Edge Case'ler
# ==========================================

def test_project_update_empty_body():
    """Kısmi güncellemede hiçbir alan verilmeyebilir (tüm alanlar None olabilmeli)."""
    schema = ProjectUpdate()
    assert schema.name is None
    assert schema.description is None


def test_project_update_partial_fields():
    """Sadece isim veya sadece açıklama güncellenebilmeli."""
    name_update = ProjectUpdate(name="Yeni Proje Adı")
    assert name_update.name == "Yeni Proje Adı"
    assert name_update.description is None

    desc_update = ProjectUpdate(description="Yeni Açıklama")
    assert desc_update.name is None
    assert desc_update.description == "Yeni Açıklama"


@pytest.mark.parametrize("invalid_name", ["", "AB", "x" * 151])
def test_project_update_invalid_name(invalid_name):
    """Güncelleme sırasında isim gönderilmişse sınır kurallarına uymak zorundadır."""
    with pytest.raises(ValidationError):
        ProjectUpdate(name=invalid_name)


# ==========================================
# 3. ProjectMemberAdd Testleri & Edge Case'ler
# ==========================================

def test_project_member_add_default_role():
    """Rol verilmediğinde varsayılan rol PARTICIPANT olmalı."""
    member = ProjectMemberAdd(user_id=10)
    assert member.user_id == 10
    assert member.role == ProjectRole.PARTICIPANT


def test_project_member_add_custom_role():
    """Geçerli bir rol verildiğinde başarıyla atanmalı."""
    member = ProjectMemberAdd(user_id=10, role=ProjectRole.OWNER)
    assert member.role == ProjectRole.OWNER


def test_project_member_add_invalid_role():
    """Tanımlı enum dışındaki bir rol (örn: 'admin') hata fırlatmalıdır."""
    with pytest.raises(ValidationError):
        ProjectMemberAdd(user_id=10, role="superadmin")


def test_project_member_add_missing_user_id():
    """user_id zorunludur, verilmezse hata fırlatmalıdır."""
    with pytest.raises(ValidationError):
        ProjectMemberAdd()


# ==========================================
# 4. ProjectResponse Testleri
# ==========================================

def test_project_response_mapping():
    """Tüm alanlar eksiksiz doldurulduğunda ProjectResponse doğru eşleşmeli."""
    now = datetime.now(timezone.utc)
    res = ProjectResponse(
        id=1,
        name="Proje 1",
        description="Açıklama",
        created_by_id=2,
        created_at=now,
        updated_at=now,
    )
    assert res.id == 1
    assert res.name == "Proje 1"
    assert res.created_by_id == 2