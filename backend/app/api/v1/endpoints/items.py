"""
Example items endpoints - template for adding new resources.
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.models.user import User
from app.api.deps import get_current_user


router = APIRouter(prefix="/items", tags=["Items"])


# Example schemas
class ItemCreate(BaseModel):
    """Item creation schema."""
    name: str
    description: str | None = None


class ItemUpdate(BaseModel):
    """Item update schema."""
    name: str | None = None
    description: str | None = None


class ItemResponse(BaseModel):
    """Item response schema."""
    id: int
    name: str
    description: str | None
    owner_id: int


# In-memory storage for demo (replace with database in production)
items_db: dict[int, dict] = {}
next_id = 1


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item: ItemCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create new item."""
    global next_id

    new_item = {
        "id": next_id,
        "name": item.name,
        "description": item.description,
        "owner_id": current_user.id,
    }
    items_db[next_id] = new_item
    next_id += 1

    return ItemResponse(**new_item)


@router.get("", response_model=List[ItemResponse])
async def list_items(
    current_user: User = Depends(get_current_user),
) -> Any:
    """List user's items."""
    user_items = [
        ItemResponse(**item)
        for item in items_db.values()
        if item["owner_id"] == current_user.id
    ]
    return user_items


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get item by ID."""
    item = items_db.get(item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    if item["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this item",
        )

    return ItemResponse(**item)


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update item."""
    item = items_db.get(item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    if item["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this item",
        )

    if item_update.name is not None:
        item["name"] = item_update.name

    if item_update.description is not None:
        item["description"] = item_update.description

    return ItemResponse(**item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete item."""
    item = items_db.get(item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    if item["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this item",
        )

    del items_db[item_id]
