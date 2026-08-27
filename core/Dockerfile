# 1. Use an official Python image
FROM python:3.11-slim-bookworm

# 2. Install system dependencies + LibreOffice (CRITICAL for your PDFs)
RUN apt-get update && apt-get install -y \
    libreoffice \
    fonts-liberation \
    libfontconfig1 \
    libpq-dev \
    gcc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Set the directory inside the container
WORKDIR /app

# 4. Install Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your project code into the container
COPY . .

# 6. Expose the port Django runs on
EXPOSE 8000

# 7. Use Gunicorn (Production Server) to run the app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]