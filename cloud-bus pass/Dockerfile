# Use an official lightweight Python runtime
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency definition and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into container
COPY . .

# Initialize database schema inside the container
RUN python init_db.py

# Expose port 5000
EXPOSE 5000

# Start production WSGI server (Gunicorn) with multi-worker concurrency
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]