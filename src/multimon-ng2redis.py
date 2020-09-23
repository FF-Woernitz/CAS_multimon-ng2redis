import re
import signal
import subprocess
import time
import RedisMBlib
from datetime import datetime

reg_zvei1 = r'ZVEI1\:\s(\d{5})'

print("starting multimon-ng2redis...")

def log(log):
    print(datetime.now(), log)

def signalhandler(signum, frame):
    log('Signal handler called with signal {}'.format(signum))
    try:
        proc.kill()
        redis_lib.exit()
    except:
        pass
    log('exiting...')
    exit()
signal.signal(signal.SIGTERM, signalhandler)
signal.signal(signal.SIGHUP, signalhandler)

last_zvei = ""
last_zvei_time = 0.0

def checkIfDoubleAlert(zvei):
    global last_zvei, last_zvei_time
    if zvei == last_zvei:
        if time.time() - last_zvei_time < 10:
            return True

    last_zvei = zvei
    last_zvei_time = time.time()

    return False

try:
    redis_lib = RedisMBlib.RedisMB()

    rgx_zvei1 = re.compile(reg_zvei1)
    proc = subprocess.Popen(['/opt/multimon-ng/multimon-ng', '-c', '-a', 'ZVEI1', '-q'], stdout=subprocess.PIPE)
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.decode('ascii').strip()
        log("new data: {}".format(line))
        regex_match = rgx_zvei1.match(line)
        if regex_match:
            if not checkIfDoubleAlert(regex_match.groups()[0]):
                log("send ZVEI to redis: {}".format(regex_match.groups()[0]))
                redis_lib.newZVEI(regex_match.groups()[0])
            else:
                log("omit sending ZVEI to redis as ZVEI is double: {}".format(regex_match.groups()[0]))
        else:
            log("send ZVEI error to redis: {}".format(line))
            redis_lib.errorZVEI(line)
            last_zvei = ""
except KeyboardInterrupt:
    signalhandler("KeyboardInterrupt", None)

