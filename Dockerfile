# Выкачиваем из dockerhub образ с python версии 3.10
FROM python:3.10

# Устанавливаем рабочую директорию для проекта в контейнере
WORKDIR /app

# Чтобы собрался pip
COPY README.md /app
COPY pyproject.toml /app
COPY main.py /app

# Волшебные константы
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Скачиваем/обновляем необходимые библиотеки для проекта 
RUN pip install --no-cache-dir --upgrade .

# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:run_app_production()"]

# |ВАЖНЫЙ МОМЕНТ| копируем содержимое папки, где находится Dockerfile, 
# в рабочую директорию контейнера
COPY . /app