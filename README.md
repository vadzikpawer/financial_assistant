# FinAssistant - Персональный Финансовый Помощник

![Tests](https://github.com/username/finassistant/actions/workflows/test-workflow.yml/badge.svg)
![Docker Build](https://github.com/username/finassistant/actions/workflows/docker-workflow.yml/badge.svg)
![Deploy](https://github.com/username/finassistant/actions/workflows/deploy-workflow.yml/badge.svg)

Продвинутый финансовый ассистент с AI-аналитикой для российских пользователей. Приложение помогает отслеживать расходы, анализировать траты и предлагает персонализированные рекомендации по экономии.

## Особенности

- 📊 Мониторинг и анализ финансовых операций
- 🏦 Интеграция с российскими банками (Тинькофф, Сбербанк и др.)
- 🤖 AI-рекомендации на основе анализа ваших трат
- 🎯 Постановка и отслеживание финансовых целей
- 📱 Адаптивный дизайн для мобильных устройств
- 🔒 Высокий уровень защиты данных

## Технический стек

- Backend: Python, Flask, SQLAlchemy
- Database: PostgreSQL
- AI: AIML API с моделью Gemma 3
- Frontend: Material Design, Chart.js
- Deployment: Docker, GitHub Actions

## Требования для запуска

- Python 3.11+
- PostgreSQL 14+
- Docker и Docker Compose (для контейнеризации)

## Локальная установка

1. Клонировать репозиторий:
   ```bash
   git clone https://github.com/username/finassistant.git
   cd finassistant
   ```

2. Создать и активировать виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   venv\Scripts\activate  # Windows
   ```

3. Установить зависимости:
   ```bash
   # Для разработки
   pip install -r dev-requirements.txt -e .
   
   # Для продакшена
   pip install -r requirements.txt
   ```

4. Создать файл `.env` с необходимыми переменными окружения:
   ```
   FLASK_APP=main.py
   FLASK_ENV=development
   SESSION_SECRET=your_secret_key
   DATABASE_URL=postgresql://username:password@localhost:5432/finassistant
   PGUSER=username
   PGPASSWORD=password
   PGDATABASE=finassistant
   PGHOST=localhost
   PGPORT=5432
   AIML_API_KEY=your_aiml_api_key
   ```

5. Запустить приложение:
   ```bash
   python main.py
   ```

## Запуск с использованием Docker

1. Клонировать репозиторий:
   ```bash
   git clone https://github.com/username/finassistant.git
   cd finassistant
   ```

2. Создать файл `.env` с переменными окружения (см. выше)

3. Запустить контейнеры с помощью Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Приложение будет доступно по адресу: http://localhost:5000

## Развертывание в production

### Предварительные требования

- Сервер с установленными Docker и Docker Compose
- Настроенный GitHub Actions для CI/CD
- Ключи доступа к серверу (SSH)

### Шаги для развертывания

1. Добавить секреты в настройки GitHub репозитория:
   - `SSH_PRIVATE_KEY` - приватный SSH ключ для доступа к серверу
   - `SSH_KNOWN_HOSTS` - файл known_hosts с записью о сервере
   - `DEPLOY_HOST` - IP-адрес или домен сервера
   - `DEPLOY_USER` - имя пользователя на сервере
   - `DEPLOY_PATH` - путь к директории на сервере

2. При пуше в ветку `main` или создании тега (например, `v1.0.0`):
   - GitHub Actions запустит тесты
   - Создаст Docker образ
   - Опубликует его в GitHub Container Registry

3. Для запуска деплоя:
   - Создать новый релиз в GitHub, или
   - Вручную запустить workflow "Deploy to Production" в GitHub Actions

4. На сервере Docker Compose автоматически:
   - Загрузит последний образ
   - Обновит контейнеры
   - Запустит приложение с новой версией

### Обновление уже развернутого приложения

1. Внести изменения в код
2. Создать Pull Request в `main`
3. После успешного прохождения тестов и ревью, смержить PR
4. GitHub Actions автоматически запустит процесс сборки и публикации образа
5. Запустить workflow "Deploy to Production" для обновления на сервере

## Запуск тестов

```bash
python run_tests.py
```

## Структура проекта

```
├── app.py                    # Основной файл приложения
├── main.py                   # Точка входа для запуска
├── models.py                 # Модели данных
├── Dockerfile                # Конфигурация Docker
├── docker-compose.yml        # Конфигурация Docker Compose
├── routers/                  # Маршруты приложения
│   ├── auth.py               # Авторизация и регистрация
│   ├── banks.py              # Управление банковскими счетами
│   ├── dashboard.py          # Дашборд
│   ├── savings.py            # Цели накоплений
│   └── transactions.py       # Транзакции
├── services/                 # Сервисы бизнес-логики
│   ├── ai_recommendation.py  # AI-рекомендации
│   ├── bank_api.py           # API для банков
│   ├── recommendation_engine.py # Движок рекомендаций
│   └── transaction_analyzer.py # Анализ транзакций
├── static/                   # Статические файлы
│   ├── css/                  # Стили
│   ├── img/                  # Изображения
│   ├── js/                   # JavaScript
│   └── manifest.json         # Манифест PWA
├── templates/                # HTML шаблоны
├── tests/                    # Тесты
└── .github/                  # GitHub Actions workflows
```

## Доступные URL

- `/` - Главная страница
- `/login` - Вход в систему
- `/register` - Регистрация
- `/dashboard` - Панель управления
- `/transactions` - Список транзакций
- `/banks` - Управление банковскими счетами
- `/connect_bank` - Подключение нового банка
- `/savings_goals` - Цели накоплений
- `/recommendations` - Рекомендации по экономии

## Лицензия

MIT

## Авторы

Команда Replit AI