# Виртуальный окружение
python3 -m venv .venv
source .venv/bin/activate
# deactivate
# rm -rf .venv

# Зависимости
python3 -m pip install poetry # Установка poetry
python3 -m poetry install # Установка зависимостей из poetry.lock
python3 -m poetry lock # Заполнение poetry.lock
# poetry install

# Запуск Docker
docker compose up --build -d
# docker kill $(docker ps -a -q)

# docker compose down
# docker compose build --no-cache
# docker compose up

# docker compose down --volumes
# docker compose up --build -d

# Проверить то что порт забит 
# sudo lsof -i :5432
# sudo systemctl stop postgresql


# Запустить app.py (bot_polling)
python3 -m src.app
PYTHONPATH=. python3 -m src.app


# Запустить app.py (bot_webhook)
# python3 -m uvicorn src.app:create_app --factory --host 0.0.0.0 --port 8000
poetry run uvicorn src.app:create_app --factory --host 0.0.0.0 --port 8001 --workers=1
python3 -m consumer


sudo lsof -i :80
sudo lsof -i :9000
sudo lsof -i :9001
sudo lsof -i :5432
sudo lsof -i :6379
sudo lsof -i :8000

chmod +x scripts/cleanup_ports.sh
./scripts/cleanup_ports.sh

sudo systemctl status nginx
sudo systemctl restart nginx


# Удалять мусор
# sudo find . -name '__pycache__' -type d -exec rm -rf {} +

# Скачать модуль в poetry
python3 -m poetry add <module_name>

# wget https://dl.min.io/client/mc/release/linux-amd64/mc
# chmod +x mc
# sudo mv mc /usr/local/bin/
# mc alias set local http://localhost:9000 minioadmin minioadmin
# mc ls local

# docker compose down
# docker compose down -v


# вывести древо проекта
# tree -I '.vscode|.venv|.mypy_cache|__pycache__'

# find . -type f \
# ! -path './.vscode/*' \
#     ! -path './node_modules/*' \
#     ! -path './.venv/*' \
#     ! -path './.mypy_cache/*' \
#     ! -path './pycache/*' \
#     ! -path './src/storage/__pycache__/*.cpython-312.pyc' \
#     ! -name '*.cpython-312.pyc' \
#     ! -path '*/__pycache__/*.pyc' \
#     ! -path './.git/*' \
#     ! -path './poetry.lock' \
#     -exec echo "Opening file: {}" \; -exec cat {} \;

# Миграции
# alembic init alembic
# add sqlalchemy.url = postgresql://postgres:mypassword@localhost:5432/mydatabase
# alembic revision --autogenerate -m "init"
# alembic/versions/<revision_id>_init.py
# alembic upgrade head
