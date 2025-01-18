ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim as base

WORKDIR /moveo

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
