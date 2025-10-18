FROM python:3.13-slim

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 4782

CMD ["python", "main.py"]