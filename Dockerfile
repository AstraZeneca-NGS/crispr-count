# syntax=docker/dockerfile:1.2

################# BASE IMAGE ######################
ARG BASE_IMAGE=python:3.11-slim-bookworm
# hadolint ignore=DL3006
FROM ${BASE_IMAGE} as build
# subdir for path to copy files into the container
ARG START_FROM='python'

################## METADATA ######################
LABEL base.image="${BASE_IMAGE}"
LABEL version="4"
LABEL software="count_guides_dual"
LABEL software.version="1.0.0"
LABEL about.summary="Dual guide count"
LABEL about.home=""
LABEL about.documentation="https://bitbucket.astrazeneca.com/projects/DA/repos/az-cruk-crispr-guide-count"
LABEL about.license="Proprietary"
LABEL about.tags="General"
LABEL extra.binaries="count.py"

################## MAINTAINER ######################
LABEL maintainer="CRUK FGC team <fgcdev@cancer.org.uk>"

################## INSTALLATION ######################
ENV WORK /tmp/build
WORKDIR ${WORK}

COPY ${START_FROM}/requirements.txt requirements.txt
RUN pip install --no-cache-dir --requirement requirements.txt && \
    rm requirements.txt

COPY ${START_FROM}/requirements-awscli.txt requirements-awscli.txt
RUN pip install --no-cache-dir --requirement requirements-awscli.txt && \
    rm requirements-awscli.txt

COPY ${START_FROM}/count.py count.py
RUN install -m 0755 count.py /usr/local/bin/count.py && \
    rm count.py

# Extra packages:
#   procps      required for usage inside make releaseNextflow,
#               so that Nextflow can poll CPU usage:
#               Command 'ps' required by nextflow to collect task metrics
RUN apt-get --assume-yes update && \
    apt-get --assume-yes --no-install-recommends install \
        procps=2:4.0.* \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -d /data pipelineuser
USER pipelineuser
WORKDIR /data/

################## FINISH UP ######################

FROM build as dev

COPY --chown=pipelineuser:pipelineuser ${START_FROM}/test test
COPY --chown=pipelineuser:pipelineuser ${START_FROM}/tests tests
COPY --chown=pipelineuser:pipelineuser ${START_FROM}/test-output test-output
COPY --chown=pipelineuser:pipelineuser ${START_FROM}/test-data test-data
COPY --chown=pipelineuser:pipelineuser ${START_FROM}/requirements-dev.txt requirements-dev.txt
COPY --chown=pipelineuser:pipelineuser ${START_FROM}/count.py count.py

RUN pip install --no-cache-dir --requirement requirements-dev.txt && \
    rm requirements-dev.txt
