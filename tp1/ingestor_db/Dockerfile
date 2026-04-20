FROM python:3.9-slim
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install --no-cache-dir psycopg2-binary hdfs
COPY main.py .
ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]