FROM tobsa/archlinux:latest
COPY src/pulse_client.conf /etc/pulse/client.conf
RUN pacman --needed --noconfirm -Syu git libpulse python3 python-pip multimon-ng
RUN pacman --noconfirm -Scc

RUN groupadd -r -g 800 cas && useradd --no-log-init -r -u 800 -g cas cas

WORKDIR /opt/multimon-ng2redis
COPY requirements.txt .
COPY src ./

ADD "https://api.github.com/repos/FF-Woernitz/CAS_lib/git/refs/heads/master" skipcache
RUN pip install --no-cache-dir -r requirements.txt

USER cas:cas
CMD ["python3", "-u", "multimon-ng2redis.py"]
