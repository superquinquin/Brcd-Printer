###################################################################################
FROM  python:3.11-slim as base

# Set apt variables to avoid interactive mode
ENV  DEBIAN_FRONTEND=noninteractive
# DL4006 info: Set the SHELL option -o pipefail before RUN with a pipe in it.
SHELL  ["/bin/bash", "-o", "pipefail", "-c"]

# Update the list of packages, install minimal packages
RUN  apt-get update \
    && apt-get install --no-install-recommends -y \
    apt-utils \
    curl \
    libpcre3 \
    libpcre3-dev \
    libssl-dev \
    build-essential \
    libjpeg62-turbo-dev \
    zlib1g-dev
# Clean apt to minimize size of image
RUN  apt-get clean
RUN  rm -rf /var/lib/apt/lists/*
# Add default user for the docker container to be used as non-root
RUN  adduser superquinquin

###################################################################################
FROM  base as pybase
# Keeps Python from generating .pyc files in the container
ENV  PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV  PYTHONUNBUFFERED=1
# Configure PIP
ENV  PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100
# Configure Poetry
ENV  POETRY_VERSION=1.7.1
# DL4006 info: Set the SHELL option -o pipefail before RUN with a pipe in it.
SHELL  ["/bin/bash", "-o", "pipefail", "-c"]
USER superquinquin
# Install poetry
RUN  curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION}


###################################################################################
FROM pybase as final

ARG  LABEL_NAME="printer"
ARG  LABEL_VERSION="0.2.0"
ARG  LABEL_URL="https://github.com/superquinquin/Brcd-Printer/"

ENV  APP_DIR="/home/superquinquin/printer"
ENV  APP_PORT=8000
ENV  APP_WORKERS=1
ENV  PATH="/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:~/.local/bin"
# Keeps Python from generating .pyc files in the container
ENV  PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV  PYTHONUNBUFFERED=1
# Setup the poetry / pip env
ENV  PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=${INSTALL_DIR}

WORKDIR  ${APP_DIR}
USER superquinquin

COPY . ${APP_DIR}/
RUN poetry install --no-interaction --no-ansi --only main

EXPOSE ${APP_PORT}
ENTRYPOINT ["sanic asgi:app --host=0.0.0.0 --port=${APP_PORT} --single-process --no-motd"]

# Label the docker image
LABEL name="${LABEL_NAME}"
LABEL version="${LABEL_VERSION}"
LABEL url="${LABEL_URL}"
