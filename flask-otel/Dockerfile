FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY app.py .

EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
