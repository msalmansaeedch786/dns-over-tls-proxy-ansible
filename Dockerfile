FROM python:alpine

WORKDIR /usr/src/app

RUN apk update && \
    apk upgrade && \
    apk add supervisor && \
    rm -rf /var/cache/apk/*

COPY ./proxy.py .

COPY ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
