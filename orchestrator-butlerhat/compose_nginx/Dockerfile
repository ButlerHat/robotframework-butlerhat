FROM nginx:latest


COPY ./desktop-lite-debian.sh /usr/share/nginx/scripts/desktop-lite-debian.sh
RUN chmod +x /usr/share/nginx/scripts/desktop-lite-debian.sh
RUN bash /usr/share/nginx/scripts/desktop-lite-debian.sh

