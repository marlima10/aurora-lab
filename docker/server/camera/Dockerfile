FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends ustreamer && rm -rf /var/lib/apt/lists/*
USER 0
ENTRYPOINT ["ustreamer", "--device=/dev/video0", "--host=0.0.0.0", "--port=8080", "--resolution=640x480", "--desired-fps=10"]
