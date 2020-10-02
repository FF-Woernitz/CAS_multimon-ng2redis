FROM lopsided/archlinux:latest AS intermediate-pacman

RUN sed -i 's/^Server/# Server/' /etc/pacman.d/mirrorlist; \
    echo 'Server = http://de3.mirror.archlinuxarm.org/$arch/$repo' >> /etc/pacman.d/mirrorlist; \
    pacman -Sy;

FROM tobsa/cmake-fixed:latest AS intermediate-builder

RUN pacman -Sy && pacman --needed --noconfirm -S libpulse git;

ADD "https://api.github.com/repos/EliasOenal/multimon-ng/git/refs/heads/master" skipcache
RUN cd /root; \
    git clone https://github.com/EliasOenal/multimon-ng.git; \
    mkdir /root/multimon-ng/build;

WORKDIR /root/multimon-ng/build

RUN cmake ..
RUN make

FROM python:3-alpine

RUN apk add --no-cache git

COPY --from=intermediate-builder /root/multimon-ng/build/multimon-ng /opt/multimon-ng
COPY src/pulse_client.conf /etc/pulse/client.conf

WORKDIR /opt/multimon-ng2redis
COPY requirements.txt .
COPY src ./

ADD "https://api.github.com/repos/FF-Woernitz/CAS_lib/git/refs/heads/master" skipcache
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "-u", "multimon-ng2redis.py"]
