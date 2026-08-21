from enum import StrEnum

class ProjectRole(StrEnum):
    OWNER = "owner"
    PARTICIPANT = "participant"


class InvitationStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REVOKED = "REVOKED"