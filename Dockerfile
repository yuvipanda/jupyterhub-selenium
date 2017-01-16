FROM debian:jessie

RUN apt-get update

RUN apt-get install --yes python3 python3-pip

RUN pip3 install nbformat selenium

ADD test.py /srv
ADD test.ipynb /srv

WORKDIR /srv

CMD python3 test.py
