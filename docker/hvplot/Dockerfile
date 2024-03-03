FROM ubuntu:24.04

LABEL maintainer="massimods@met.no"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y dist-upgrade && apt-get install -y apt-utils  build-essential git python3.12-venv python3.12-dev libpython3.12-dev libnetcdf-dev

RUN ls -la /usr/bin
ENV VIRTUAL_ENV=/opt/venv
RUN python3.12 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies:
COPY requirements.txt .
RUN pip install -U pip
RUN pip install -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 7000

ENV ORIGIN="0.0.0.0:7000" PORT="7000" PREFIX="" LOG_LEVEL="debug"

COPY ./app /app
ENTRYPOINT ["./entrypoint.sh"]
