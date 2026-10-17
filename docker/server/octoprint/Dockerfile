ARG PYTHON_BASE_IMAGE=3.12-slim-bookworm

FROM python:${PYTHON_BASE_IMAGE} AS build

ARG octoprint_ref=1.11.8
ENV octoprint_ref ${octoprint_ref:-master}

RUN apt-get update && apt-get install -y \
  avrdude \
  build-essential \
  cmake \
  curl \
  imagemagick \
  ffmpeg \
  fontconfig \
  g++ \
  git \
  haproxy \
  libffi-dev \
  libjpeg-dev \
  libjpeg62-turbo \
  libprotobuf-dev \
  libudev-dev \
  libusb-1.0-0-dev \
  libv4l-dev \
  openssh-client \
  v4l-utils \
  xz-utils \
  zlib1g-dev \
  x265

RUN curl -fsSL 'https://github.com/just-containers/s6-overlay/releases/download/v3.2.3.2/s6-overlay-noarch.tar.xz' -o '/tmp/s6-overlay-noarch.tar.xz' && echo '5379750ed30a84bbd2e2dd74847ba6b5bd29cd0b2e3ea2ec58049b57eb2eda12  /tmp/s6-overlay-noarch.tar.xz' | sha256sum -c - && tar -C / -Jxpf '/tmp/s6-overlay-noarch.tar.xz' && curl -fsSL 'https://github.com/just-containers/s6-overlay/releases/download/v3.2.3.2/s6-overlay-x86_64.tar.xz' -o '/tmp/s6-overlay-x86_64.tar.xz' && echo 'e6befcc96a437a3831386ecfc51808c5d3e939dc5fe3c02ae9284599e8aa2408  /tmp/s6-overlay-x86_64.tar.xz' | sha256sum -c - && tar -C / -Jxpf '/tmp/s6-overlay-x86_64.tar.xz'

# Install octoprint
RUN	curl -fsSLO --compressed --retry 3 --retry-delay 10 \
  https://github.com/OctoPrint/OctoPrint/archive/${octoprint_ref}.tar.gz \
	&& mkdir -p /opt/octoprint \
  && tar xzf ${octoprint_ref}.tar.gz --strip-components 1 -C /opt/octoprint --no-same-owner

WORKDIR /opt/octoprint
RUN python -m pip install --no-cache-dir 'pip<26' 'setuptools<81' wheel && python -m pip install .
RUN mkdir -p /octoprint/octoprint /octoprint/plugins

# Install mjpg-streamer
RUN curl -fsSLO --compressed --retry 3 --retry-delay 10 \
  https://github.com/jacksonliam/mjpg-streamer/archive/master.tar.gz \
  && mkdir /mjpg \
  && tar xzf master.tar.gz -C /mjpg


WORKDIR /mjpg/mjpg-streamer-master/mjpg-streamer-experimental
RUN make
RUN make install

# Copy services into s6 servicedir and set default ENV vars
COPY root /
COPY root/octoprint/octoprint/config.yaml /etc/aurora/octoprint-defaults.yaml
RUN chmod 0755 /etc/cont-init.d/02-aurora-defaults
ENV CAMERA_DEV /dev/video0
ENV MJPG_STREAMER_INPUT -n -r 640x480
ENV PIP_USER true
ENV PYTHONUSERBASE /octoprint/plugins
ENV PATH "${PYTHONUSERBASE}/bin:${PATH}"
# set WORKDIR
WORKDIR /octoprint

# port to access haproxy frontend
EXPOSE 80

VOLUME /octoprint

ENTRYPOINT ["/init"]

# AuroraServer: plugins preservados e instalados na imagem, fora do volume.
COPY plugins.lock.json download-plugins.py /tmp/aurora-source/
RUN python3 /tmp/aurora-source/download-plugins.py
COPY plugins.lock.json /opt/aurora-plugins.lock.json
COPY costestimation-static.py /tmp/costestimation-static.py
COPY prepare-source.py /tmp/prepare-source.py
RUN python3 /tmp/prepare-source.py && PIP_USER=false python3 -m pip install --no-cache-dir /tmp/aurora-plugins/*.zip && rm -rf /tmp/aurora-plugins
COPY compatibility.py /tmp/aurora-compatibility.py
RUN python3 /tmp/aurora-compatibility.py
COPY haproxy.cfg /etc/haproxy/haproxy.cfg
RUN haproxy -c -f /etc/haproxy/haproxy.cfg
# O checkout Windows pode trazer CRLF em arquivos sem extensao.
RUN sed -i 's/\r$//' /etc/cont-init.d/01-mjpg-streamer-config /etc/cont-init.d/v3-dir-structure-check /etc/services.d/*/run && sed -i '1s|^#!/usr/bin/with-contenv|#!/command/with-contenv|' /etc/cont-init.d/01-mjpg-streamer-config /etc/cont-init.d/v3-dir-structure-check /etc/services.d/*/run && sed -i '1s|^#!/usr/bin/execlineb|#!/command/execlineb|' /etc/services.d/*/run && chmod 0755 /etc/cont-init.d/01-mjpg-streamer-config /etc/cont-init.d/v3-dir-structure-check /etc/services.d/*/run
