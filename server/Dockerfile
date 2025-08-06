# ВЕРСИЯ 0.0.1
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY requirements_no_version.txt .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements_no_version.txt

# Создание директории для Yandex Cloud конфигурации
RUN mkdir -p /app/yandex-cloud-config

# Копирование исходного кода приложения
COPY . .

# Экспонирование порта
EXPOSE 8000

# Команда для запуска приложения
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"] 