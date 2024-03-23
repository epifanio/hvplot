# pull official base image
FROM python:3.12.2-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get -y dist-upgrade && apt-get install -y apt-utils \
 build-essential \
 git \
 libnetcdf-dev


# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt


ENV ORIGIN="0.0.0.0:7000" PORT="7000" PREFIX="" LOG_LEVEL="debug"

WORKDIR /usr/src/app

