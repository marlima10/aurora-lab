FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/tmp TZ=America/Sao_Paulo
WORKDIR /app
COPY common.py store.py tools.py api.py connector.py worker.py ./
USER 65534:65534
CMD ["python", "api.py"]

FROM base AS engine
USER root
COPY requirements-engine.lock /tmp/requirements-engine.lock
ADD --checksum=sha256:cea79a194377908d8bdddcec945ad29585023914e80602a54076d0efacbd9b90 https://codeload.github.com/open-jarvis/OpenJarvis/tar.gz/5a9b5268f2432f7ea4fe402e384ecb6b64a649bb /tmp/upstream.tar.gz
RUN mkdir /opt/openjarvis && tar -xzf /tmp/upstream.tar.gz --strip-components=1 -C /opt/openjarvis \
 && rm /tmp/upstream.tar.gz \
 && pip install --no-cache-dir -r /tmp/requirements-engine.lock \
 && PYTHONPATH=/opt/openjarvis/src python -c "from openjarvis.engine.ollama import OllamaEngine; print('OpenJarvis engine import verified')"
ENV PYTHONPATH=/opt/openjarvis/src JARVIS_NUM_CTX=8192
COPY engine_service.py ./
USER 65534:65534
CMD ["python", "engine_service.py"]

FROM base AS whisper
USER root
COPY requirements-whisper.lock /tmp/requirements-whisper.lock
RUN pip install --no-cache-dir -r /tmp/requirements-whisper.lock
COPY speech_service.py prepare_models.py ./
USER 65534:65534
ENV SPEECH_ROLE=transcribe OMP_NUM_THREADS=2
CMD ["python", "speech_service.py"]

FROM base AS piper
USER root
COPY requirements-piper.lock /tmp/requirements-piper.lock
RUN pip install --no-cache-dir -r /tmp/requirements-piper.lock
COPY speech_service.py ./
USER 65534:65534
ENV SPEECH_ROLE=synthesize OMP_NUM_THREADS=1
CMD ["python", "speech_service.py"]

FROM base AS research
USER root
COPY requirements-research.lock /tmp/requirements-research.lock
RUN pip install --no-cache-dir -r /tmp/requirements-research.lock
USER 65534:65534
ENV CONNECTOR_ROLE=research
CMD ["python", "connector.py"]
