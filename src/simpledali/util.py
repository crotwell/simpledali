
from datetime import datetime, timedelta, timezone
import jwt # pip3 install pyjwt (not jwt!!!)


def datetimeToHPTime(time):
    hptime = int(time.timestamp() * MICROS)
    return hptime

def hptimeToDatetime(hptime):
    dt = datetime.utcfromtimestamp( float(hptime) / MICROS)
    return dt

def utcnowWithTz():
    return datetime.now(timezone.utc)

def encodeAuthToken(user_id, expireDelta, writePattern, secretKey):
    """
    Generates a ringserver Auth Token
    user_id: user name
    expireDelta: lifetime of token, ex timedelta(days=1, seconds=60)
    writePattern: streamid reg exp, ex 'XX_.*/MTRIG'
    secretKey: encryption pass phrase, should be > 32, longer is ok
    :return: string, base64 encoded signed jwt token
    """
    payload = {
        'exp': utcnowWithTz() + expireDelta,
        'iat': utcnowWithTz(),
        'sub': user_id,
        'wpat': writePattern
    }
    encoded = jwt.encode(
        payload,
        secretKey,
        algorithm='HS256'
    )
    return encoded

def decodeAuthToken(encodedToken, secretKey):
    return jwt.decode(encodedToken, secretKey, algotithms='HS256')

def timeUntilExpireToken(token):
    payload = jwt.decode(token, verify=False)
    return datetime.fromtimestamp(payload["exp"], timezone.utc) - utcnowWithTz()
