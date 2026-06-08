from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import select
from starlette.requests import Request

from app.auth.keys import generate_api_key
from app.auth.permissions import Permission
from app.common.api.errors import HTTP400, HTTP404
from app.common.api.paginate import PaginatedResponse
from app.core.config import settings
from app.core.database import DBSession, get_db
from app.organization.models.api_key import (
    OrganizationApiKey,
    OrganizationApiKeyBasic,
    OrganizationApiKeyCreateResponse,
)

router = APIRouter(prefix='/organization/api-keys', tags=['organization'], dependencies=[Depends(Permission.is_admin)])

MAX_API_KEYS_PER_ORG = 10


class ApiKeyCreate(BaseModel):
    """Request body for creating a public API key."""

    name: str = Field(min_length=1, max_length=200, description='Human-readable label for the key')


@router.get('', response_model=PaginatedResponse[OrganizationApiKeyBasic], name='api-key-list')
def list_api_keys(
    request: Request, db: DBSession = Depends(get_db), page: int = 1
) -> PaginatedResponse[OrganizationApiKeyBasic]:
    """List the admin organization's API keys (never returns the token)."""
    base_query = OrganizationApiKey.request_query(request, db).order_by(OrganizationApiKey.id.desc())  # ty: ignore[unresolved-attribute]
    paginated_query = base_query.limit(settings.dft_page_size).offset((page - 1) * settings.dft_page_size)
    page_keys = db.exec(paginated_query).all()
    items = [OrganizationApiKeyBasic(**key.model_dump()) for key in page_keys]
    total = db.exec(select(func.count()).select_from(base_query.subquery())).one()
    return PaginatedResponse[OrganizationApiKeyBasic](
        items=items, total=total, page=page, page_size=settings.dft_page_size
    )


@router.post('', status_code=201, response_model=OrganizationApiKeyCreateResponse, name='api-key-create')
def create_api_key(
    data: ApiKeyCreate, request: Request, db: DBSession = Depends(get_db)
) -> OrganizationApiKeyCreateResponse:
    """Create a new public API key for the admin's organization.

    Returns the full key exactly once; only the last4 and SHA-256 hash are stored.
    """
    organization_id = request.state.user.organization_id
    key_count = db.exec(
        select(func.count())
        .select_from(OrganizationApiKey)
        .where(OrganizationApiKey.organization_id == organization_id)
    ).one()
    if key_count >= MAX_API_KEYS_PER_ORG:
        raise HTTP400(f'Maximum of {MAX_API_KEYS_PER_ORG} API keys per organization reached')
    full_key, last4, hashed_key = generate_api_key()
    api_key = db.create(
        OrganizationApiKey(organization_id=organization_id, name=data.name, hashed_key=hashed_key, last4=last4)
    )
    return OrganizationApiKeyCreateResponse(**api_key.model_dump(), key=full_key)


@router.delete('/{api_key_id}', status_code=204, name='api-key-delete')
def delete_api_key(api_key_id: int, request: Request, db: DBSession = Depends(get_db)) -> None:
    """Delete an API key. Scoped to the admin's organization (404 if it belongs to another)."""
    api_key = db.exec(
        OrganizationApiKey.request_query(request, db).where(OrganizationApiKey.id == api_key_id)
    ).one_or_none()
    if api_key is None:
        raise HTTP404('API key not found')
    db.delete(api_key)
    db.commit()
