from fastapi import HTTPException, status

from app.models import ApplicationStatus

ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.SUBMITTED: {ApplicationStatus.FIELD_VERIFICATION},
    ApplicationStatus.FIELD_VERIFICATION: {ApplicationStatus.READY_FOR_DECISION},
    ApplicationStatus.READY_FOR_DECISION: {
        ApplicationStatus.APPROVED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.RETURNED,
    },
    ApplicationStatus.RETURNED: {ApplicationStatus.SUBMITTED, ApplicationStatus.FIELD_VERIFICATION},
    ApplicationStatus.APPROVED: set(),
    ApplicationStatus.REJECTED: set(),
}


def assert_transition(current: ApplicationStatus, target: ApplicationStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Invalid transition from {current.value} to {target.value}. "
                f"Allowed: {sorted(s.value for s in allowed) or ['none']}"
            ),
        )
