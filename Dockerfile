# originally designed for Docker version: 18.09.1

# 3 means latest 3.x
ARG PYTHON_TAG=3-alpine

# largely arbitrary
ARG COLDFRONT_DIR=/usr/src/app


# base python image is specified via build arg
FROM python:${PYTHON_TAG} AS base-python


FROM base-python

ARG COLDFRONT_DIR
WORKDIR "${COLDFRONT_DIR}"

## basic requirements
COPY requirements.txt \
     ./
RUN pip install --user --no-cache-dir -r requirements.txt

## coldfront app files w/o config
COPY . \
     ./

## with sample config
COPY ./coldfront/config/local_strings.py.sample \
     ./coldfront/config/local_strings.py
COPY ./coldfront/config/local_settings.py.sample \
     ./coldfront/config/local_settings.py

RUN ./manage.py initial_setup
RUN ./manage.py load_test_data

EXPOSE 80
# TODO: ENTRYPOINT w/ helper script (see best practices)
#       would be roughly: ENTRYPOINT ./docker-entrypoint.sh
CMD ./manage.py runserver
