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
RUN  useradd -rm -d "/home/superquinquin" -s "/bin/bash" -u 1001 superquinquin

###################################################################################
FROM  base as pybase

ENV  DEBIAN_FRONTEND=noninteractive
# Keeps Python from generating .pyc files in the container
ENV  PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV  PYTHONUNBUFFERED=1
# Configure PIP
ENV  APP_DIR="/home/superquinquin/app"
ENV  PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME="/home/superquinquin/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR="/tmp/poetry_cache"
# Configure Poetry
ENV  POETRY_VERSION=1.8.2
# DL4006 info: Set the SHELL option -o pipefail before RUN with a pipe in it.
SHELL  ["/bin/bash", "-o", "pipefail", "-c"]
USER superquinquin
# Install poetry
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN  curl -sSL https://install.python-poetry.org | /usr/local/bin/python3 - --version ${POETRY_VERSION}
WORKDIR $APP_DIR
COPY poetry.lock pyproject.toml ./
# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --only main && rm -rf $POETRY_CACHE_DIR


###################################################################################
FROM pybase as final

ARG  LABEL_NAME="printer"
ARG  LABEL_VERSION="0.3.0"
ARG  LABEL_URL="https://github.com/superquinquin/Brcd-Printer/"

ENV  APP_DIR="/home/superquinquin/app"
ENV PATH="$POETRY_HOME/bin:$PATH"
# Keeps Python from generating .pyc files in the container
ENV  PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV  PYTHONUNBUFFERED=1
# Setup the poetry / pip env

ENV  PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/home/superquinquin/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
    POETRY_CACHE_DIR="/tmp/poetry_cache"

WORKDIR  ${APP_DIR}
USER superquinquin

COPY --chown=superquinquin:superquinquin --from=pybase ${POETRY_HOME} ${POETRY_HOME}
COPY --chown=superquinquin:superquinquin . ${APP_DIR}/

EXPOSE 8000
ENTRYPOINT ["poetry", "run", "sanic", "asgi:app", "--host=0.0.0.0", "--port=8000", "--single-process", "--no-motd"]

# Label the docker image
LABEL name="${LABEL_NAME}"
LABEL version="${LABEL_VERSION}"
LABEL url="${LABEL_URL}"
