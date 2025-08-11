FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Make port 8501 available to the world outside this container (Streamlit app)
EXPOSE 8501

# Define environment variable for streamlit to run headlessly
ENV STREAMLIT_SERVER_HEADLESS=true

# Run app.py when the container launches
CMD ["streamlit", "run", "app.py"]
