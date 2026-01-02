# Учёт аренды

[![en](https://img.shields.io/badge/lang-en-blue.svg)](README.md)
[![ru](https://img.shields.io/badge/lang-ru-green.svg)](README.ru.md)

[![CI](https://github.com/YOUR_USERNAME/rental-housing/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/rental-housing/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/rental-housing/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/rental-housing)

Django-приложение для учёта арендных платежей: договоры, ставки аренды, платежи и денежные транзакции.

## Возможности

- Управление договорами аренды с поддержкой нескольких валют (RUB, USD, EUR)
- История ставок аренды с периодами действия
- Учёт арендных и дополнительных платежей
- Денежные транзакции для сверки платежей
- Поддержка русского и английского языков
- Автоматическая тёмная/светлая тема (по настройкам системы)
- Подсказки по платежам с автоматическим расчётом (JavaScript)

## Требования

- Python 3.13+
- uv (менеджер пакетов)

## Установка

```bash
# Клонировать репозиторий
git clone <repo-url>
cd rental-housing

# Настроить окружение
cp .env.example .env

# Установить зависимости и создать виртуальное окружение
make setup

# Применить миграции
make migrate

# Запустить сервер разработки
make runserver
```

Приложение будет доступно по адресу http://127.0.0.1:8000

## Основные команды

```bash
make setup              # Первоначальная настройка
make runserver          # Запуск сервера
make migrate            # Применить миграции
make makemigrations     # Создать миграции
make test               # Запуск тестов (pytest)
make test-cov           # Тесты с отчётом о покрытии
make lint               # Проверка кода (ruff)
make format             # Форматирование кода (ruff)
make audit              # Проверка уязвимостей (pip-audit)
make check              # Проверка + аудит + тесты
```

## Структура проекта

```
rental-housing/
├── leases/                 # Основное приложение
│   ├── models.py           # Модели данных
│   ├── views.py            # Представления
│   ├── forms.py            # Формы
│   ├── templates/          # Шаблоны
│   ├── static/             # Статические файлы (CSS, JS)
│   └── tests/              # Тесты (pytest)
├── rental_housing/         # Конфигурация проекта
├── locale/                 # Файлы переводов
├── .github/workflows/      # GitHub Actions CI
├── conftest.py             # Фикстуры pytest
└── Makefile                # Команды для разработки
```

## CI/CD

Проект использует GitHub Actions для непрерывной интеграции:
- Линтинг кода (ruff)
- Аудит безопасности зависимостей (pip-audit)
- Запуск тестов с отчётом о покрытии
- Интеграция с Codecov

После создания репозитория на GitHub:
1. Замените `YOUR_USERNAME` в бейджах на ваше имя пользователя
2. Добавьте `CODECOV_TOKEN` в секреты репозитория (Settings → Secrets → Actions)

## Лицензия

MIT
