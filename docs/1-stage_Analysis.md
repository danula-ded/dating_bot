# **Описание сервисов Dating Bot**

## 🏗 **Архитектура Telegram-бота**

### 📱 **Клиентская часть**

- **Telegram Client** - мобильное приложение пользователя.
- **Polling/Webhook** - механизм получения обновлений от Telegram.

### 🖥 **Серверная часть (Producer)**

- **Основной сервер**:
  - Принимает запросы от Telegram.
  - Обрабатывает команды пользователей.
  - Формирует ответы.

### 🗄 **Хранение данных**

- **PostgreSQL** - основная база данных.
- **Minio (S3-совместимое хранилище)** - хранение медиа (фото, видео).
- **Redis**:
  - Кэширование частых запросов.
  - Хранение временных данных (сессии, состояния).

### 🔄 **Асинхронная обработка (Consumer)**

- **RabbitMQ** - очередь сообщений для:
  - Долгих операций
  - Фоновых задач
- **Consumer-сервер** - обработка задач из очереди.

### 📊 **Мониторинг**

- **Prometheus** - сбор метрик:
  - Производительность
  - Ошибки
  - Нагрузка

![Посмотрите в папке есть картинка](./Arhitecthure.jpg)

### **1. Основные компоненты:**

1. **Frontend** → Telegram Bot (`aiogram`).
2. **Backend Services** → FastAPI (RESTful API).
3. **Database** → PostgreSQL (основные данные) + Redis (кэш).
4. **Storage** → MinIO (S3-совместимое хранилище для фото).
5. **Message Broker** → RabbitMQ (для событий: лайки, пропуски, мэтчи).
6. **Celery** → Фоновые задачи (пересчет рейтинга, очистка кэша).

---

### **2. Схема базы данных (PostgreSQL)**

#### **Основные таблицы:**

#### **🔹 `users`**

```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,         -- Telegram ID
    username VARCHAR(64),               -- @username
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64),
    age INTEGER CHECK (age >= 18),      -- Ограничение: 18+
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    city VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### **🔹 `profiles`**

```sql
CREATE TABLE profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    bio TEXT,
    interests JSONB,                   -- Список интересов: ["музыка", "спорт"]
    photo_urls TEXT[],                 -- Ссылки на фото в MinIO (S3)
    preferred_gender VARCHAR(10),      -- Кого ищет пользователь
    preferred_age_min INTEGER,         -- Минимальный возраст для поиска
    preferred_age_max INTEGER,         -- Максимальный возраст для поиска
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **🔹 `ratings`**

```sql
CREATE TABLE ratings (
    rating_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    primary_score FLOAT DEFAULT 0,     -- Баллы за анкету (0-10)
    behavioral_score FLOAT DEFAULT 0,  -- Баллы за активность (0-10)
    total_rating FLOAT GENERATED ALWAYS AS (primary_score * 0.6 + behavioral_score * 0.4) STORED,
    last_updated TIMESTAMP DEFAULT NOW()
);
```

---

### **3. Пример данных в БД**

#### **Таблица `users`**

| user_id | username   | first_name | age | gender | city   |
| ------- | ---------- | ---------- | --- | ------ | ------ |
| 123456  | @ivan_2023 | Иван       | 25  | male   | Москва |

#### **Таблица `profiles`**

| profile_id | user_id | bio                 | interests          | photo_urls        |
| ---------- | ------- | ------------------- | ------------------ | ----------------- |
| 1          | 123456  | "Люблю путешествия" | ["музыка", "горы"] | ["s3/photo1.jpg"] |

#### **Таблица `ratings`**

| rating_id | user_id | primary_score | behavioral_score | total_rating |
| --------- | ------- | ------------- | ---------------- | ------------ |
| 1         | 123456  | 8.5           | 7.2              | 8.02         |

---

### **4. Где что хранится?**

| Данные                | Хранилище  |
| --------------------- | ---------- |
| Профили пользователей | PostgreSQL |
| Фотографии            | MinIO (S3) |
| Кэш анкет             | Redis      |
| Очереди событий       | RabbitMQ   |
