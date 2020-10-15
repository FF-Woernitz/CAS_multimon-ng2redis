import re, signal, subprocess, time
from CASlib import Logger, RedisMB, Config
from logbook import INFO, NOTICE, WARNING
from datetime import datetime, time as dtime
from pytz import timezone

log = Logger.Logger("multimon-ng2redis").getLogger()
config = Config.Config().getConfig()

reg_zvei1 = r'ZVEI1\:\s(\d{5})'

log.log(INFO, "starting multimon-ng2redis...")


def signalhandler(signum, frame):
    log.log(INFO, 'Signal handler called with signal {}'.format(signum))
    try:
        proc.kill()
        redis_lib.exit()
    except:
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
    begin_time = dtime(trigger["testalarm"]["hour_start"], trigger["testalarm"]["minute_start"])
    end_time = dtime(trigger["testalarm"]["hour_end"], trigger["testalarm"]["minute_end"])
    now = datetime.now(timezone("Europe/Berlin"))
    return now.weekday() == trigger["testalarm"]["weekday"] and begin_time <= now.time() <= end_time

try:
    redis_lib = RedisMB.RedisMB()

    rgx_zvei1 = re.compile(reg_zvei1)
    proc = subprocess.Popen(['/opt/multimon-ng/multimon-ng', '-c', '-a', 'ZVEI1', '-q'], stdout=subprocess.PIPE)
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
                redis_lib.inputZVEI(zvei)
                for key, config in config['trigger'].items():
                    if key == zvei:
                        if isTestAlert(config):
                            redis_lib.testalertZVEI(zvei)
                        else:
                            redis_lib.alertZVEI(zvei)
            else:
                log.log(INFO, "omit sending ZVEI to redis as ZVEI is double: {}".format(zvei))
        else:
            log.log(WARNING, "send ZVEI error to redis: {}".format(line))
            redis_lib.errorZVEI(line)
            last_zvei = ""
except KeyboardInterrupt:
    signalhandler("KeyboardInterrupt", None)
