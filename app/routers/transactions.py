import math
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.database import get_db
from app.models import Category, Transaction, User
from app.schemas import (
    CategoryOut,
    TransactionCreate,
    TransactionOut,
    TransactionPage,
    TransactionUpdate,
    TxType,
    UserOut,
    from_kopecks,
    to_kopecks,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


def tx_to_out(tx: Transaction) -> TransactionOut:
    return TransactionOut(
        id=tx.id,
        amount=from_kopecks(tx.amount_kopecks),
        type=tx.type,
        date=tx.date,
        comment=tx.comment,
        category=CategoryOut.model_validate(tx.category),
        user=UserOut.model_validate(tx.user),
    )


def get_active_category(db: Session, category_id: int, tx_type: str) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    if category.type != tx_type:
        raise HTTPException(status_code=422, detail="Тип категории не совпадает с типом операции")
    return category


@router.get("", response_model=TransactionPage)
def list_transactions(
    date_from: date_type | None = None,
    date_to: date_type | None = None,
    category_id: int | None = None,
    user_id: int | None = None,
    type: TxType | None = None,
    q: str | None = Query(default=None, description="Поиск по комментарию"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Transaction).options(
        joinedload(Transaction.category), joinedload(Transaction.user)
    )
    if date_from is not None:
        query = query.filter(Transaction.date >= date_from)
    if date_to is not None:
        query = query.filter(Transaction.date <= date_to)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)
    if type is not None:
        query = query.filter(Transaction.type == type)
    if q:
        query = query.filter(func.casefold(Transaction.comment).like(f"%{q.casefold()}%"))

    total = query.count()
    items = (
        query.order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return TransactionPage(
        items=[tx_to_out(tx) for tx in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, math.ceil(total / per_page)),
    )


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(
    body: TransactionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_active_category(db, body.category_id, body.type)
    tx = Transaction(
        user_id=user.id,
        category_id=body.category_id,
        type=body.type,
        amount_kopecks=to_kopecks(body.amount),
        date=body.date,
        comment=body.comment,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx_to_out(tx)


@router.patch("/{tx_id}", response_model=TransactionOut)
def update_transaction(
    tx_id: int,
    body: TransactionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    tx = db.get(Transaction, tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    if body.category_id is not None:
        get_active_category(db, body.category_id, tx.type)
        tx.category_id = body.category_id
    if body.amount is not None:
        tx.amount_kopecks = to_kopecks(body.amount)
    if body.date is not None:
        tx.date = body.date
    if body.comment is not None:
        tx.comment = body.comment
    db.commit()
    db.refresh(tx)
    return tx_to_out(tx)


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    tx = db.get(Transaction, tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    db.delete(tx)
    db.commit()
