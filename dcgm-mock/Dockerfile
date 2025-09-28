FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./
# Copy fixtures explicitly into /app/fixtures so they're always available at runtime
COPY fixtures /app/fixtures

# Fail the build early if fixtures didn't get copied (helps catch context/.dockerignore issues)
RUN if [ ! -d /app/fixtures ]; then echo "ERROR: /app/fixtures missing in build image" && ls -la /app || true; exit 1; fi || true
EXPOSE 9100
CMD ["python", "app.py"]
