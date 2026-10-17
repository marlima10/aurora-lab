FROM python:3.13-slim
WORKDIR /app
COPY power.py /app/power.py
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "/app/power.py"]
