# syntax=docker/dockerfile:1
FROM python:3.12 as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y \
        g++ \
        python3-dev \
        python3-setuptools \
        gdal-bin \
        openssh-client \
        postgresql-client \
        gettext \
        binutils \
        libgdal-dev && \
    GDAL_VERSION=$(gdal-config --version) && \
    pip3 install "pygdal>=${GDAL_VERSION}.0,<=${GDAL_VERSION}.999" && \
    apt-get remove -y \
        g++ \
        python3-dev \
        python3-setuptools \
        libgdal-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY ./config/requirements.txt .

RUN pip install -r requirements.txt

COPY ./backend .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]