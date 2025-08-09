FROM python:3.13.6-slim
LABEL org.opencontainers.image.source=https://github.com/ArntBergin/kulturbotten


WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80" ]
