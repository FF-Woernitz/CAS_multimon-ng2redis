import re
import signal
import subprocess
import time

from logbook import INFO, NOTICE, WARNING, DEBUG

from CASlibrary import Config, Logger, RedisMB
from CASlibrary.constants import AlertType

log = Logger.Logger("multimon-ng2redis").getLogger()
config = Config.Config().getConfig()

reg_zvei1 = r'ZVEI1\:\s(\d[\dE]{4})'

log.log(INFO, "starting multimon-ng2redis...")


def signalhandler(signum):
    log.log(INFO, 'Signal handler called with signal {}'.format(signum))
    try:
        proc.kill()
        redis_lib.exit()
    except Exception:
        pass
    log.log(NOTICE, 'exiting...')
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


def fixDoubleDigitInZvei(zvei):
    """
    multimon-ng does not correctly recognize double digits in ZVEI.
    If a ZVEI has a double digit the second digit uses the frequency 2600, multimon-ng detects this as a "E".

    This function will use the digit before the "E" in the fixed ZVEI.
    :param str zvei:
    :return str fixedZVEI:
    """
    fixedZVEI = ""
    for index, digit in enumerate(zvei):
        if digit == "E":
            if index == 0:
                raise IndexError("E on first digit of ZVEI: " + zvei)
            fixedZVEI += zvei[index - 1]
        else:
            fixedZVEI += digit
    return fixedZVEI

try:
    redis_lib = RedisMB.RedisMB()

    rgx_zvei1 = re.compile(reg_zvei1)
    proc = subprocess.Popen(
        ['/usr/bin/multimon-ng', '-c', '-a', 'ZVEI1', '-q'],
        stdout=subprocess.PIPE)
    while True:
        line = proc.stdout.readline()
        if not line:
            continue
        line = line.decode('ascii').strip()
        log.log(DEBUG, "new raw data: {}".format(line))
        regex_match = rgx_zvei1.match(line)
        if regex_match:
            zvei = regex_match.groups()[0]
            zvei = fixDoubleDigitInZvei(zvei)
            log.log(INFO, "new data: {}".format(zvei))
            if not checkIfDoubleAlert(zvei):
                log.log(INFO, "send ZVEI to redis: {}".format(zvei))
                redis_lib.input(AlertType.ZVEI, zvei)
            else:
                log.log(INFO, "omit sending ZVEI to redis as ZVEI is double: {}".format(zvei))
        else:
            if line == "F":
                log.log(INFO, "omit ZVEI as it is a siren code: {}".format(line))
            else:
                log.log(WARNING, "send ZVEI error to redis: {}".format(line))
                redis_lib.error(AlertType.ZVEI, line)
            last_zvei = ""
except KeyboardInterrupt:
    signalhandler("KeyboardInterrupt")
