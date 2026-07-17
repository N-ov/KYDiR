"""CLI для управления KYDiR.

    python manage.py init-db
    python manage.py add-user --username masha --name "Маша" --color "#e05c5c"
    python manage.py seed-categories
"""
import argparse
import getpass
import sys

from app.auth import hash_password
from app.database import SessionLocal, init_db
from app.models import Category, User

DEFAULT_CATEGORIES = [
    # (name, type, icon, color)
    ("Продукты", "expense", "🛒", "#4caf50"),
    ("Кафе и рестораны", "expense", "🍽️", "#ff9800"),
    ("Транспорт", "expense", "🚗", "#2196f3"),
    ("Жильё", "expense", "🏠", "#795548"),
    ("Коммуналка и связь", "expense", "💡", "#607d8b"),
    ("Здоровье", "expense", "💊", "#e91e63"),
    ("Одежда", "expense", "👕", "#9c27b0"),
    ("Развлечения", "expense", "🎮", "#673ab7"),
    ("Дети", "expense", "🧸", "#ffc107"),
    ("Подарки", "expense", "🎁", "#f44336"),
    ("Прочее", "expense", "📦", "#9e9e9e"),
    ("Зарплата", "income", "💼", "#4caf50"),
    ("Подработка", "income", "💻", "#2196f3"),
    ("Подарки", "income", "🎁", "#ff9800"),
    ("Прочее", "income", "💰", "#9e9e9e"),
]


def cmd_init_db(_args) -> None:
    init_db()
    print("База инициализирована.")


def cmd_add_user(args) -> None:
    init_db()
    password = args.password or getpass.getpass("Пароль: ")
    if len(password) < 4:
        sys.exit("Пароль должен быть не короче 4 символов.")
    with SessionLocal() as db:
        username = args.username.strip().lower()
        if db.query(User).filter(User.username == username).first():
            sys.exit(f"Пользователь '{username}' уже существует.")
        db.add(User(
            username=username,
            display_name=args.name or args.username,
            color=args.color,
            password_hash=hash_password(password),
        ))
        db.commit()
    print(f"Пользователь '{username}' создан.")


def cmd_seed_categories(_args) -> None:
    init_db()
    with SessionLocal() as db:
        added = 0
        for name, tx_type, icon, color in DEFAULT_CATEGORIES:
            exists = db.query(Category).filter(
                Category.name == name, Category.type == tx_type
            ).first()
            if exists:
                continue
            db.add(Category(name=name, type=tx_type, icon=icon, color=color))
            added += 1
        db.commit()
    print(f"Добавлено категорий: {added}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Управление KYDiR")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Создать таблицы базы данных")

    p_user = sub.add_parser("add-user", help="Добавить члена семьи")
    p_user.add_argument("--username", required=True)
    p_user.add_argument("--name", help="Отображаемое имя (по умолчанию = username)")
    p_user.add_argument("--color", default="#4f8ef7", help="Цвет пользователя в hex")
    p_user.add_argument("--password", help="Пароль (если не указать — спросит интерактивно)")

    sub.add_parser("seed-categories", help="Создать стартовый набор категорий")

    args = parser.parse_args()
    {"init-db": cmd_init_db, "add-user": cmd_add_user, "seed-categories": cmd_seed_categories}[args.command](args)


if __name__ == "__main__":
    main()
