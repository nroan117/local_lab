FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY collector.py /usr/local/bin/collector.py
RUN chmod +x /usr/local/bin/collector.py
CMD ["/usr/local/bin/collector.py"]
