# Базовый образ с Python
FROM python:3.11-slim

# Установка рабочей директории
WORKDIR /app

# Копирование requirements.txt
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY main.py .

# Команда для запуска бота
CMD ["python", "main.py"]
