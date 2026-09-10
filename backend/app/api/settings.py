"""
Read-only settings/status endpoints.

Azure DevOps integration is configured server-side only (see
backend/app/core/config.py) — the PAT never leaves the backend and must
never appear in any response from this file.
"""
from fastapi import APIRouter, Depends

from ..db.models import User
from ..core.dependencies import get_current_user
from ..services.azure_devops_service import AzureDevOpsService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/azure-connection-status")
def azure_connection_status(current_user: User = Depends(get_current_user)):
    """Real status of the server's configured Azure DevOps credential —
    org/project are not secret and safe to return; the PAT itself is
    never included here."""
    service = AzureDevOpsService()
    configured = service.is_configured
    connected = service.check_connection() if configured else False
    return {
        "configured": configured,
        "connected": connected,
        "org": service.org or None,
        "project": service.project or None,
    }
