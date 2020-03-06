FROM centos:latest

RUN dnf -y install python3
RUN pip3 install "virtualenv<20"

RUN mkdir /tmp/requirements/
ADD requirements.txt \
    test-requirements.txt \
    /tmp/requirements/

RUN cat /tmp/requirements/* > /tmp/requirements/requirements_all.txt

RUN virtualenv /venv
RUN /venv/bin/pip install -r /tmp/requirements/requirements_all.txt

CMD ["bash"]
