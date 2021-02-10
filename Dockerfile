FROM lopsided/archlinux:latest AS intermediate-pacman

RUN sed -i 's/^Server/# Server/' /etc/pacman.d/mirrorlist;
RUN echo 'Server = http://de3.mirror.archlinuxarm.org/$arch/$repo' >> /etc/pacman.d/mirrorlist;
RUN pacman --needed --noconfirm -Syu;

FROM intermediate-pacman AS intermediate-builder

RUN pacman --needed --noconfirm -S libpulse git base-devel cmake;

ADD "https://api.github.com/repos/EliasOenal/multimon-ng/git/refs/heads/master" skipcache
RUN cd /root;
RUN git clone https://github.com/EliasOenal/multimon-ng.git;
RUN mkdir /root/multimon-ng/build;

WORKDIR /root/multimon-ng/build

RUN cmake ..
RUN make

FROM intermediate-pacman

COPY --from=intermediate-builder /root/multimon-ng/build/multimon-ng /opt/multimon-ng/multimon-ng
COPY src/pulse_client.conf /etc/pulse/client.conf

RUN pacman --needed --noconfirm -S git libpulse python3 python-pip
RUN pacman --noconfirm -Scc

RUN groupadd -r -g 800 cas && useradd --no-log-init -r -u 800 -g cas cas

WORKDIR /opt/multimon-ng2redis
COPY requirements.txt .
COPY src ./

ADD "https://api.github.com/repos/FF-Woernitz/CAS_lib/git/refs/heads/master" skipcache
RUN pip install --no-cache-dir -r requirements.txt

USER cas:cas
CMD ["python3", "-u", "multimon-ng2redis.py"]
