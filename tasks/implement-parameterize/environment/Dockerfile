FROM python:3.12-slim

# pytest is only for the agent's convenience (visible tests). The grader uses
# nothing but the standard library.
RUN pip install --no-cache-dir pytest==8.3.3

WORKDIR /app
COPY app/ /app/
