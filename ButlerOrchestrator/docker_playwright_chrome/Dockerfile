# Dockerfile for chrome
FROM mcr.microsoft.com/playwright:v1.39.0-jammy

# Remove user with UID 1000 and GID 1000
RUN userdel -r pwuser

COPY docker-scripts/*.sh /tmp/docker-scripts/
RUN bash /tmp/docker-scripts/common-debian.sh "true" "vscode" "1000" "1000" "true" "true" "true" \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/* /tmp/docker-scripts

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends poppler-utils ffmpeg libsm6 libxext6

# Install chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get -y install ./google-chrome-stable_current_amd64.deb
RUN rm google-chrome-stable_current_amd64.deb

# To make this work user must have sudo and things in common-debian.sh
COPY docker-scripts/desktop-lite-debian.sh /tmp/docker-scripts/
RUN apt-get update && bash /tmp/docker-scripts/desktop-lite-debian.sh
ENV DBUS_SESSION_BUS_ADDRESS="autolaunch:" \
    VNC_RESOLUTION="1440x768x16" \
    VNC_DPI="96" \
    VNC_PORT="5901" \
    NOVNC_PORT="6080" \
    DISPLAY=":1" \
    LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8"

# RUN mkdir -p /home/vscode/playwright && chown -R vscode:vscode /home/vscode/playwright
WORKDIR /home/vscode
COPY playwright/ playwright/
WORKDIR /home/vscode/playwright
RUN npm install

USER vscode
WORKDIR /home/vscode
COPY entrypoint.sh entrypoint.sh
ENTRYPOINT ["bash", "entrypoint.sh"]
# CMD ["sleep", "infinity"]
