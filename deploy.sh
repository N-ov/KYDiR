#!/usr/bin/env bash
# Деплой KYDiR на VPS. Запускать из Git Bash (Windows) или любого терминала с ssh.
#
#   ./deploy.sh setup     — первичная настройка VPS (docker, клон репозитория, запуск)
#   ./deploy.sh           — обновление: git pull + пересборка + перезапуск
#   ./deploy.sh adduser   — добавить члена семьи (интерактивно спросит пароль)
#   ./deploy.sh logs      — логи приложения
#   ./deploy.sh backup    — скачать файл базы с VPS в ./backups/
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
    echo "Нет файла .env — скопируйте .env.example в .env и заполните." >&2
    exit 1
fi
set -a; source .env; set +a

: "${VPS_HOST:?Заполните VPS_HOST в .env}"
: "${VPS_USER:?Заполните VPS_USER в .env}"

SSH_OPTS=(-p "${VPS_PORT:-22}")
[[ -n "${VPS_SSH_KEY:-}" ]] && SSH_OPTS+=(-i "$VPS_SSH_KEY")
REMOTE="$VPS_USER@$VPS_HOST"
APP_DIR="${VPS_APP_DIR:-/opt/kydir}"

run() { ssh "${SSH_OPTS[@]}" "$REMOTE" "$@"; }

cmd_setup() {
    echo "==> Проверяю docker на VPS..."
    run "command -v docker >/dev/null || curl -fsSL https://get.docker.com | sh"

    echo "==> Клонирую/обновляю репозиторий..."
    run "if [ -d '$APP_DIR/.git' ]; then cd '$APP_DIR' && git pull; else git clone '$REPO_URL' '$APP_DIR'; fi"

    echo "==> Копирую .env на VPS..."
    scp "${SSH_OPTS[@]/#-p/-P}" .env "$REMOTE:$APP_DIR/.env"

    echo "==> Собираю и запускаю..."
    run "cd '$APP_DIR' && docker compose up -d --build"

    echo "==> Инициализирую базу и категории..."
    run "cd '$APP_DIR' && docker compose exec app python manage.py init-db && docker compose exec app python manage.py seed-categories"

    echo
    echo "Готово. Теперь добавьте членов семьи:  ./deploy.sh adduser"
    echo "Приложение: http://$VPS_HOST/  (или https://\$DOMAIN, если настроен домен)"
}

cmd_deploy() {
    echo "==> Обновляю код и перезапускаю..."
    run "cd '$APP_DIR' && git pull && docker compose up -d --build"
    scp "${SSH_OPTS[@]/#-p/-P}" .env "$REMOTE:$APP_DIR/.env" >/dev/null
    echo "Готово."
}

cmd_adduser() {
    read -rp "Логин: " username
    read -rp "Отображаемое имя: " name
    read -rp "Цвет (hex, напр. #4f8ef7): " color
    run -t "cd '$APP_DIR' && docker compose exec app python manage.py add-user --username '$username' --name '$name' --color '${color:-#4f8ef7}'"
}

cmd_logs() { run "cd '$APP_DIR' && docker compose logs -f --tail=100 app"; }

cmd_backup() {
    mkdir -p backups
    local dest="backups/kydir-$(date +%Y%m%d-%H%M%S).db"
    run "cd '$APP_DIR' && docker compose exec app sqlite3 /app/data/kydir.db '.backup /app/data/backup.db'" \
        || run "cd '$APP_DIR' && cp data/kydir.db data/backup.db"
    scp "${SSH_OPTS[@]/#-p/-P}" "$REMOTE:$APP_DIR/data/backup.db" "$dest"
    run "rm -f '$APP_DIR/data/backup.db'"
    echo "База сохранена в $dest"
}

case "${1:-deploy}" in
    setup)   cmd_setup ;;
    deploy)  cmd_deploy ;;
    adduser) cmd_adduser ;;
    logs)    cmd_logs ;;
    backup)  cmd_backup ;;
    *) echo "Использование: $0 [setup|deploy|adduser|logs|backup]" >&2; exit 1 ;;
esac
