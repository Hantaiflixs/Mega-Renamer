FROM python:3.11-slim

WORKDIR /app

# system deps for mega.py may require libssl, etc. Install common ones
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set env for production to avoid .env usage
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
