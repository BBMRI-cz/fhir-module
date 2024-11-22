FROM python:3.11-alpine
RUN apk add --no-cache --upgrade bash
RUN apk add --no-cache curl bash
ENV APP_DIR="/opt/fhir-module"
ENV RECORDS_DIR="/opt/records"
RUN mkdir -p $APP_DIR $RECORDS_DIR
WORKDIR $APP_DIR
COPY --chown=1001:1001 . .
RUN pip install --no-cache-dir -r requirements.txt
USER 1001
CMD ["python", "main.py"]