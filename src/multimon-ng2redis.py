import re
import signal
import subprocess
import time
from datetime import datetime, time as dtime

from CASlibrary import Config, Logger, RedisMB
from CASlibrary.constants import AlertType

from logbook import INFO, NOTICE, WARNING

from pytz import timezone

log = Logger.Logger("multimon-ng2redis").getLogger()
config = Config.Config().getConfig()

reg_zvei1 = r'ZVEI1\:\s(\d{5})'

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


def isTestAlert(trigger):
    if "testalert" in trigger:
        begin_time = dtime(trigger["testalert"]["hour_start"], trigger["testalert"]["minute_start"])
        end_time = dtime(trigger["testalert"]["hour_end"], trigger["testalert"]["minute_end"])
        now = datetime.now(timezone("Europe/Berlin"))
        return now.weekday() == trigger["testalert"]["weekday"] and begin_time <= now.time() <= end_time
    else:
        return False


try:
    redis_lib = RedisMB.RedisMB()

    rgx_zvei1 = re.compile(reg_zvei1)
    proc = subprocess.Popen(
        ['/usr/bin/multimon-ng', '-c', '-a', 'ZVEI1', '-q'],
        stdout=subprocess.PIPE)
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.decode('ascii').strip()
        log.log(INFO, "new data: {}".format(line))
        regex_match = rgx_zvei1.match(line)
        if regex_match:
            zvei = regex_match.groups()[0]
            if not checkIfDoubleAlert(zvei):
                log.log(INFO, "send ZVEI to redis: {}".format(zvei))
                redis_lib.input(AlertType.ZVEI, zvei)
                for key, config_trigger in config['trigger'].items():
                    if key == zvei:
                        if isTestAlert(config_trigger):
                            redis_lib.test(AlertType.ZVEI, zvei)
                        else:
                            redis_lib.alert(AlertType.ZVEI, zvei)
            else:
                log.log(INFO,
                        "omit sending ZVEI to redis as ZVEI "
                        "is double: {}".format(zvei))
        else:
            if line == "F":
                log.log(INFO, "omit ZVEI as it is a siren code: {}".format(line))
            else:
                log.log(WARNING, "send ZVEI error to redis: {}".format(line))
                redis_lib.error(AlertType.ZVEI, line)
            last_zvei = ""
except KeyboardInterrupt:
    signalhandler("KeyboardInterrupt")
