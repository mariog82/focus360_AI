
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared ./shared
COPY services/wellness_service ./services/wellness_service
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["gunicorn","-b","0.0.0.0:8000","services.wellness_service.app:app"]
