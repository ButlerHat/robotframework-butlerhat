FROM mcr.microsoft.com/devcontainers/miniconda:0-3

ARG UNAME=vscode
ARG USER_ID=1000
ARG GROUP_ID=1000
ARG GITHUB_TOKEN

# This image already has a user vscode
USER root
# RUN groupmod -g $GROUP_ID $UNAME
# RUN usermod -u $USER_ID -g $GROUP_ID $UNAME

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends poppler-utils ffmpeg libsm6 libxext6 cron

RUN wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && dpkg -i cloudflared-linux-amd64.deb

ENV PATH=/home/$UNAME/.local/bin:$PATH

# Copy RobotLibraries.
RUN mkdir /tmp/pip-tmp && chmod -R 777 /tmp && chmod -R 777 /opt/conda
USER $UNAME
COPY conda.yaml /tmp/pip-tmp/conda.yaml
COPY .devcontainer/resolve_conda_secret.py /tmp/pip-tmp/resolve_conda_secret.py

WORKDIR /tmp/pip-tmp
RUN python resolve_conda_secret.py --token $GITHUB_TOKEN
RUN conda env update -n base -f conda_pass.yaml

# Create web conda environment.
COPY web/conda.yaml /tmp/pip-tmp/conda_web.yaml
RUN conda env create -f conda_web.yaml

WORKDIR /workspaces
RUN rm -rf /tmp/pip-tmp

ENV TZ='/usr/share/zoneinfo/Europe/Madrid'

# Run cron service after container is started. sudo service cron start
# RUN sudo service cron start
