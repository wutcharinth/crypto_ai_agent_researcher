FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose port (Railway will override this with $PORT, but good practice)
EXPOSE 8000

# Run the FastAPI app using Uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
