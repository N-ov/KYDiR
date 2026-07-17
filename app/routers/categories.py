from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Category, Transaction, User
from app.schemas import CategoryCreate, CategoryOut, CategoryUpdate, TxType

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    type: TxType | None = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Category)
    if type is not None:
        q = q.filter(Category.type == type)
    if not include_archived:
        q = q.filter(Category.archived == False)  # noqa: E712
    return q.order_by(Category.name).all()


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(body: CategoryCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    category = Category(**body.model_dump())
    db.add(category)
    db.commit()
    return category


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    body: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Удаляем только пустые категории; с операциями — архивируйте (PATCH archived=true)."""
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    has_transactions = db.query(Transaction.id).filter(Transaction.category_id == category_id).first()
    if has_transactions:
        raise HTTPException(
            status_code=409,
            detail="У категории есть операции — вместо удаления заархивируйте её",
        )
    db.delete(category)
    db.commit()
