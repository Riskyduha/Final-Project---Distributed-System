FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Default RabbitMQ envs can be overridden by docker-compose
ENV RABBITMQ_HOST=rabbitmq \
    RABBITMQ_PORT=5672

CMD ["python", "app.py"]
