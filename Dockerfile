# TODO: is there a standard LABEL for this comment?
# originally designed for Docker version: 18.09.1

## TODO: should base use debian? perhaps alpine+debian for testing?
# per https://hub.docker.com/_/python/?tab=description
# potential rationale:
#     debian vs. alpine: use different libc implementations
#     debian - glibc
#     alpine - musl
# overly loooooong comment thread for pro/cons:
#     https://news.ycombinator.com/item?id=10782897
#
# 3 means latest 3.x
ARG PYTHON_TAG=3-alpine
# pin wheel version to mitigate cache incongruencies
#     TODO: CI check to assure this is latest
ARG WHEEL_VERSION=0.33.6

# these are largely arbitrary
ARG COLDFRONT_DIR=/usr/src/app
# TODO: COLDFRONT_USER is working fine for everything except COPY --chown ...
#     in the interim, hardcoding in COPY --chown =\
ARG COLDFRONT_USER=django
# for COPY --chown to work well, must have same UID and GID or else Docker
# assumes something for you
ARG COLDFRONT_UID_GID=1984


# base python image is specified via build arg
FROM python:${PYTHON_TAG} AS base-python


FROM base-python

ARG WHEEL_VERSION
ARG COLDFRONT_DIR
ARG COLDFRONT_USER
ARG COLDFRONT_UID_GID

# optimize build cache slightly, for wheel
RUN pip install --no-cache-dir wheel=="${WHEEL_VERSION}"

## set up user:group, umask, workdir, drop root
RUN addgroup --gid "${COLDFRONT_UID_GID}" "${COLDFRONT_USER}" \
    && adduser \
        --system \
        --disabled-password \
        # set GECOS to a more restrictive umask:
        --gecos ',,,,umask=0027' \
        --uid "${COLDFRONT_UID_GID}" \
        --ingroup "${COLDFRONT_USER}" \
        "${COLDFRONT_USER}"

RUN mkdir -p "${COLDFRONT_DIR}" \
    && chown "${COLDFRONT_USER}:${COLDFRONT_USER}" "${COLDFRONT_DIR}" \
    && chmod -R o='' "${COLDFRONT_DIR}"
USER "${COLDFRONT_USER}"
WORKDIR "${COLDFRONT_DIR}"

## basic requirements
COPY --chown=django \
    requirements.txt \
    ./
RUN pip install --user --no-cache-dir -r requirements.txt

## coldfront app files w/o config
# TODO: .dockerignore (~.gitignore'd files + a few more)
COPY --chown=django \
     . \
     ./

COPY --chown=django \
     ./coldfront/config/local_strings.py.sample \
     ./coldfront/config/local_strings.py
COPY --chown=django \
     ./coldfront/config/local_settings.py.sample \
     ./coldfront/config/local_settings.py

RUN ./manage.py initial_setup
RUN ./manage.py load_test_data

EXPOSE 80
# TODO: ENTRYPOINT w/ helper script (see best practices)
#       would be roughly: ENTRYPOINT ./docker-entrypoint.sh
CMD ./manage.py runserver
