# StoryBox Frontend (Streamlit) - Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 storybox && \
    chown -R storybox:storybox /app

# Copy requirements
COPY requirements-frontend.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-frontend.txt

# Copy application code
COPY app/ ./app/
COPY webapp/ ./webapp/
COPY configs/ ./configs/

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Switch to non-root user
USER storybox

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "webapp/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
