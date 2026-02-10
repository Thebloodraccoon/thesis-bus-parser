FROM python:3.11-slim

ENV TZ=Europe/Kyiv
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    wget \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm-dev \
    libasound2 \
    libpangocairo-1.0-0 \
    libcups2 \
    libxshmfence1 \
    libglu1-mesa \
    libxcursor1 \
    libgtk-3-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libcairo-gobject2 \
    libxi6 \
    libxtst6 \
    libxrender1 \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt


# Copy application code
COPY . /app

CMD ["sh", "-c", "alembic upgrade head && python app/main.py"]