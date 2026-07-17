from datetime import date as date_type

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Category, Transaction, User
from app.schemas import CategoryTotal, MonthPoint, Summary, UserTotal, from_kopecks

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=Summary)
def summary(
    date_from: date_type | None = None,
    date_to: date_type | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Итоги за период. Без параметров — текущий месяц."""
    today = date_type.today()
    if date_from is None:
        date_from = today.replace(day=1)
    if date_to is None:
        date_to = today

    period = (Transaction.date >= date_from, Transaction.date <= date_to)

    totals = dict(
        db.query(Transaction.type, func.sum(Transaction.amount_kopecks))
        .filter(*period)
        .group_by(Transaction.type)
        .all()
    )
    income_total = from_kopecks(totals.get("income") or 0)
    expense_total = from_kopecks(totals.get("expense") or 0)

    def by_category(tx_type: str) -> list[CategoryTotal]:
        rows = (
            db.query(
                Category.id,
                Category.name,
                Category.icon,
                Category.color,
                func.sum(Transaction.amount_kopecks),
                func.count(Transaction.id),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .filter(*period, Transaction.type == tx_type)
            .group_by(Category.id)
            .order_by(func.sum(Transaction.amount_kopecks).desc())
            .all()
        )
        return [
            CategoryTotal(
                category_id=r[0], name=r[1], icon=r[2], color=r[3],
                total=from_kopecks(r[4]), count=r[5],
            )
            for r in rows
        ]

    user_rows = (
        db.query(
            User.id,
            User.display_name,
            User.color,
            func.sum(Transaction.amount_kopecks),
        )
        .join(Transaction, Transaction.user_id == User.id)
        .filter(*period, Transaction.type == "expense")
        .group_by(User.id)
        .order_by(func.sum(Transaction.amount_kopecks).desc())
        .all()
    )

    return Summary(
        date_from=date_from,
        date_to=date_to,
        income_total=income_total,
        expense_total=expense_total,
        balance=round(income_total - expense_total, 2),
        expense_by_category=by_category("expense"),
        income_by_category=by_category("income"),
        expense_by_user=[
            UserTotal(user_id=r[0], display_name=r[1], color=r[2], total=from_kopecks(r[3]))
            for r in user_rows
        ],
    )


@router.get("/monthly", response_model=list[MonthPoint])
def monthly(
    months: int = Query(default=12, ge=1, le=60),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Доходы/расходы по месяцам за последние N месяцев (для графика динамики)."""
    today = date_type.today()
    year = today.year
    month = today.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    start = date_type(year, month, 1)

    month_expr = func.strftime("%Y-%m", Transaction.date)
    rows = (
        db.query(month_expr, Transaction.type, func.sum(Transaction.amount_kopecks))
        .filter(Transaction.date >= start)
        .group_by(month_expr, Transaction.type)
        .all()
    )
    data: dict[str, dict[str, float]] = {}
    for month_key, tx_type, total in rows:
        data.setdefault(month_key, {"income": 0.0, "expense": 0.0})[tx_type] = from_kopecks(total)

    # заполняем пропущенные месяцы нулями, чтобы график был непрерывным
    points: list[MonthPoint] = []
    y, m = start.year, start.month
    for _i in range(months):
        key = f"{y:04d}-{m:02d}"
        values = data.get(key, {})
        points.append(MonthPoint(
            month=key,
            income=values.get("income", 0.0),
            expense=values.get("expense", 0.0),
        ))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return points
