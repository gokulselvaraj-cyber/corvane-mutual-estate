FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY corvane_fraud ./corvane_fraud
COPY prompts ./prompts
ENV PORT=8090
EXPOSE 8090
USER 10001
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8090/health')"
CMD ["uvicorn", "corvane_fraud.app:app", "--host", "0.0.0.0", "--port", "8090"]
