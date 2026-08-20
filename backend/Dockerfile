FROM python:3.14-slim

WORKDIR /app

# adfs-auth is declared in pyproject.toml as a path dependency on this machine's
# sibling folder (C:\Users\Eitam\adfs-auth), outside this repo and outside any normal
# Docker build context. docker-compose.yml supplies that folder here as a second,
# named build context ("adfs-auth"). pyproject.toml's dependency line is a Windows
# absolute path, which can't resolve inside this Linux image, so the sed below
# rewrites it (in this build stage only — the real pyproject.toml on disk is
# untouched) to point at where that context lands.
#
# Once adfs-auth is published to the closed network's internal package mirror (see
# CLOSED_NETWORK_MIGRATION.md, section 2), delete this COPY, the sed line, and the
# `additional_contexts` entry in docker-compose.yml — change pyproject.toml's
# dependency to a normal version pin (`adfs-auth>=0.1.0`) and this Dockerfile needs no
# special handling at all.
COPY --from=adfs-auth . /adfs-auth

COPY pyproject.toml ./
RUN sed -i 's#adfs-auth @ file:///C:/Users/Eitam/adfs-auth#adfs-auth @ file:///adfs-auth#' pyproject.toml

COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts

RUN pip install --no-cache-dir -e ".[dev]"

COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
