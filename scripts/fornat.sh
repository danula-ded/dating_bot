# Проверка форматирования
poetry run black .

# Проверка типов
poetry run mypy .

# Проверка сортировки импортов
poetry run isort .

# Проверка линтером
poetry run flake8

# Проверка кода на ошибки
poetry run pylint .