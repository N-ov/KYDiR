from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user, hash_password
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(User).order_by(User.id).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Любой член семьи может добавить нового. Открытой регистрации нет."""
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="Имя пользователя уже занято")
    user = User(
        username=body.username,
        display_name=body.display_name,
        color=body.color,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    return user


@router.patch("/me", response_model=UserOut)
def update_me(body: UserUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.display_name is not None:
        user.display_name = body.display_name
    if body.color is not None:
        user.color = body.color
    if body.password is not None:
        user.password_hash = hash_password(body.password)
    db.commit()
    return user
