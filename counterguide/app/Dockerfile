# CounterGuide application tier image for ECS Fargate (linux/amd64).
# Build:  docker build --platform linux/amd64 -t counterguide:latest app/
FROM public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py catalog.py ./

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "90", "app:app"]
