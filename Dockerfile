FROM tobsa/archlinux:devel  AS intermediate-builder
RUN df -h
RUN pacman --needed --noconfirm -Syu libpulse git cmake ca-certificates ca-certificates-utils;

RUN df -h
ADD "https://api.github.com/repos/EliasOenal/multimon-ng/git/refs/heads/master" skipcache
RUN cd /root
RUN git clone https://github.com/EliasOenal/multimon-ng.git /root/multimon-ng
RUN ls /root
RUN mkdir /root/multimon-ng/build
RUN df -h

WORKDIR /root/multimon-ng/build

RUN df -h
RUN cmake ..
RUN make

FROM tobsa/archlinux:latest

COPY --from=intermediate-builder /root/multimon-ng/build/multimon-ng /opt/multimon-ng/multimon-ng
COPY src/pulse_client.conf /etc/pulse/client.conf
RUN df -h
RUN pacman --needed --noconfirm -Syu git libpulse python3 python-pip
RUN pacman --noconfirm -Scc

RUN groupadd -r -g 800 cas && useradd --no-log-init -r -u 800 -g cas cas

WORKDIR /opt/multimon-ng2redis
COPY requirements.txt .
COPY src ./

ADD "https://api.github.com/repos/FF-Woernitz/CAS_lib/git/refs/heads/master" skipcache
RUN pip install --no-cache-dir -r requirements.txt

USER cas:cas
CMD ["python3", "-u", "multimon-ng2redis.py"]
