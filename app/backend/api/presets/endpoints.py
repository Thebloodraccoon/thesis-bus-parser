from typing import List

from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session

from app.backend.api.auth.utils import require_analytic_or_admin
from app.backend.api.presets.schema import FilterPreset, FilterPresetCreate, FilterPresetUpdate
from app.backend.api.presets.utils import FilterPresetsCRUD

from app.backend.settings import settings, get_db
from app.core.models import User

router = APIRouter(prefix="/presets", tags=["Presets"])


@router.get("/", response_model=List[FilterPreset])
async def get_filter_presets(
    _: User = Depends(require_analytic_or_admin),
):
    presets = await FilterPresetsCRUD.get_presets(_.id)
    return presets


@router.post("/", response_model=FilterPreset)
async def create_filter_preset(
    preset: FilterPresetCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_analytic_or_admin),
):
    new_preset = await FilterPresetsCRUD(db).create_preset(_.id, preset)
    return new_preset


@router.patch("/{preset_id}", response_model=FilterPreset)
async def update_filter_preset(
    preset_id: str,
    preset_update: FilterPresetUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_analytic_or_admin),
):
    updated_preset = await FilterPresetsCRUD(db).update_preset(
        _.id, preset_id, preset_update
    )
    return updated_preset


@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter_preset(
    preset_id: str,
    _: User = Depends(require_analytic_or_admin),
):
    await FilterPresetsCRUD.delete_preset(_.id, preset_id)

