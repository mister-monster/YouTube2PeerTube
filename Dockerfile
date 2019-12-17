FROM debian:stretch-slim
ENV DEBIAN_FRONTEND noninteractive
WORKDIR /app/

RUN apt update
RUN apt -y install nginx python3 python3-pip
RUN pip3 install pafy youtube_dl feedparser requests requests_toolbelt toml

COPY * /app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
