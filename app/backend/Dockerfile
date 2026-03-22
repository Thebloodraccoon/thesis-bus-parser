FROM python:3.10-slim

ENV TZ=Europe/Kyiv
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/code

WORKDIR /code

COPY app/backend/requirements.txt /code/requirements.txt

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /code/requirements.txt

COPY . /code/

CMD ["python", "-m", "app.backend.main"]