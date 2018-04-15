FROM ubuntu:latest

RUN apt-get update \
&& apt-get install -qyy \
    -o APT::Install-Recommends=false -o APT::Install-Suggests=false \
    virtualenv locales wget \
&& apt-get clean

RUN locale-gen en_US.UTF-8  
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8

RUN virtualenv -p python3 venv

COPY requirements.txt /app/
RUN . /venv/bin/activate; pip install -U pip ; pip install -r /app/requirements.txt

COPY francekultur.py /app/
WORKDIR /app
ENTRYPOINT ["/venv/bin/python","francekultur.py"]
CMD []