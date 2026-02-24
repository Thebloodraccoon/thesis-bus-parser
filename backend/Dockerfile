FROM python:3.11

WORKDIR /code

COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /code/backend/

ENV PYTHONPATH=/code

CMD ["sh", "-c", "cd backend && alembic upgrade head && cd .. && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]