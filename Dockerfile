FROM lopsided/archlinux:latest AS intermediate-pacman

RUN sed -i 's/^Server/# Server/' /etc/pacman.d/mirrorlist; \
    echo 'Server = http://de3.mirror.archlinuxarm.org/$arch/$repo' >> /etc/pacman.d/mirrorlist; \
    pacman -Sy;

FROM tobsa/cmake-fixed:latest AS intermediate-builder

RUN pacman -Sy && pacman --needed --noconfirm -S libpulse git; \
    cd /root;

ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache
RUN git clone https://github.com/EliasOenal/multimon-ng.git; \
    mkdir /root/multimon-ng/build;

WORKDIR /root/multimon-ng/build

RUN cmake ..
RUN make

FROM intermediate-pacman

RUN pacman --needed --noconfirm -S git libpulse python3 python-pip python-redis && pacman --noconfirm -Scc

RUN mkdir -p /opt/multimon-ng; \
    mkdir -p /opt/logs; \
    mkdir /opt/multimon-ng2redis; \
    groupadd -r python && useradd --no-log-init -r -g python python

ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache
RUN python3 -m pip install git+https://github.com/FF-Woernitz/CAS_lib.git;

COPY --from=intermediate-builder /root/multimon-ng/build/multimon-ng /opt/multimon-ng
COPY src/multimon-ng2redis.py /opt/multimon-ng2redis/
COPY src/client.conf /etc/pulse/
WORKDIR /opt/multimon-ng2redis
USER python:python

ENTRYPOINT ["python3", "-u", "multimon-ng2redis.py"]