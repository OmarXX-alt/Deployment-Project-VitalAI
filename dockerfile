# - Initialy, yse of python as the base for this project
FROM python:3.11-slim AS base

# - Set the working directory in the container
WORKDIR /app
# Copy requirements.txt to the working directory, saved as a separate layer for better caching of dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
# no application layer yet
COPY . .

# Since Render is in use: Expose the Port the application will run on
ENV PORT=5000
ENV INIT_DB=false
EXPOSE $PORT

# Using gunicron for production, running a shell to resolve $PORT at runtime
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --workers 2 main.server.app:app"]

