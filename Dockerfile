FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

LABEL org.opencontainers.image.source="https://github.com/ArntBergin/kulturbotten"

WORKDIR /app
COPY . .

# Installer Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Installer bare Chromium for mindre størrelse
RUN playwright install chromium

# Lag poster-mappe og gi skrivetillatelse
RUN mkdir -p /posters && chmod 777 /posters

EXPOSE 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
