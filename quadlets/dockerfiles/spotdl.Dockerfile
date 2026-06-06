FROM docker.io/library/python:3.12-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir spotdl fastapi uvicorn python-multipart
ENV HOME=/tmp
WORKDIR /app
COPY spotdl_server.py /app/spotdl_server.py
