FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml loader.ini ./
COPY corvane_loader ./corvane_loader
RUN pip install --no-cache-dir .
USER 10001
CMD ["python", "-m", "corvane_loader.billing"]
