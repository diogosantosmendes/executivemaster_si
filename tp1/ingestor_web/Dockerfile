FROM python:3.9-slim
RUN pip install requests hdfs pandas
WORKDIR /app
COPY main.py .
ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]