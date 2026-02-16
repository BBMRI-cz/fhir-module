FROM python:3.11-alpine
RUN apk add --no-cache --upgrade bash
RUN apk add --no-cache curl bash
ENV APP_DIR="/opt/fhir-module"
ENV RECORDS_DIR="/opt/records"
RUN mkdir -p $APP_DIR $RECORDS_DIR /var/log/fhir-module && \
    chown -R 1001:1001 /var/log/fhir-module
WORKDIR $APP_DIR
COPY --chown=1001:1001 . .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn
USER 1001
CMD ["gunicorn","--preload" ,"-w", "1", "-b", "0.0.0.0:5000", "main:app"]