
FROM python:3.11-slim
 
# cups-bsd gives us the `lp` binary without the full CUPS server
RUN apt-get update && apt-get install -y --no-install-recommends \
    cups-bsd \
    && rm -rf /var/lib/apt/lists/*
 

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
 
COPY app.py .
 
EXPOSE 5000

CMD ["python","app.py"]
