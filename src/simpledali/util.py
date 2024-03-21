from datetime import datetime, timezone
import jwt  # pip3 install pyjwt (not jwt!!!)

MICROS = 1000000


def datetimeToHPTime(time):
    """
    Convert a datatime.datetime to a datalink hptime
    """
    hptime = int(time.timestamp() * MICROS)
    return hptime


def hptimeToDatetime(hptime):
    """
    Convert a datalink hptime to a datatime.datetime
    """
    dt = datetime.fromtimestamp(float(hptime) / MICROS, timezone.utc)
    return dt


def utcnowWithTz():
    """
    Create a datetime to the current time with the timezone set to utc.
    """
    return datetime.now(timezone.utc)

def isowithz(dt):
    """
    A ISO8601 string for the given datatime, but with the timezone set to Z
    instead of +00:00
    """
    return dt.isoformat().replace('+00:00', 'Z')

def hptimeAsIso(hptime):
    """
    Convert an hptime into an ISO8601 string with Z timezone
    """
    return isowithz(hptimeToDatetime(hptime).isoformat())


def optional_date(date_str):
    if len(date_str) < 10:
        # some date items are just `-`,
        return None
    # this is probably dangerous...
    try:
        d = date_str
        if (len(date_str) == 19 or len(date_str) == 26) and date_str[10] == " ":
            d = f"{date_str[0:10]}T{date_str[11:]}"
        if d[-1] == "Z":
            # python datetime doesn't like Z
            d = d[:-1] + "+00:00"
        return datetime.fromisoformat(d).replace(tzinfo=timezone.utc)
    except:
        print(f"Can't parse date: {date_str}")
        return date_str

INFO_VERSION = "Version"
INFO_SERVERID = "ServerID"
INFO_CAPABILITIES = "Capabilities"
INFO_STATUS = "Status"
INFO_STREAMLIST= "StreamList"
INFO_STREAM= "Stream"

def prettyPrintInfo(info):
    out = ""
    if INFO_VERSION in info:
        out += f"  Version: {info[INFO_VERSION]}\n"
    if INFO_SERVERID in info:
        out += f"  ServerID: {info[INFO_SERVERID]}\n"
    if INFO_CAPABILITIES in info:
        out += f"  Capabilities: {info[INFO_CAPABILITIES]}\n"
    if INFO_STATUS in info:
        status = info[INFO_STATUS]
        out +=  "  Status:\n"
        out += f"    StartTime: {isowithz(status['StartTime'])}\n"
        out += f"    RingVersion: {status['RingVersion']}\n"
        out += f"    RingSize: {status['RingSize']}\n"
        out += f"    PacketSize: {status['PacketSize']}\n"
        out += f"    MaximumPacketID: {status['MaximumPacketID']}\n"
        out += f"    MaximumPackets: {status['MaximumPackets']}\n"
        out += f"    MemoryMappedRing: {status['MemoryMappedRing']}\n"
        out += f"    VolatileRing: {status['VolatileRing']}\n"
        out += f"    TotalConnections: {status['TotalConnections']}\n"
        out += f"    TotalStreams: {status['TotalStreams']}\n"
        out += f"    TXPacketRate: {status['TXPacketRate']}\n"
        out += f"    TXByteRate: {status['TXByteRate']}\n"
        out += f"    RXPacketRate: {status['RXPacketRate']}\n"
        out += f"    RXByteRate: {status['RXByteRate']}\n"
        out += f"    EarliestPacketID: {status['EarliestPacketID']}\n"
        out += f"    EarliestPacketCreationTime: {isowithz(status['EarliestPacketCreationTime'])}\n"
        out += f"    EarliestPacketDataStartTime: {isowithz(status['EarliestPacketDataStartTime'])}\n"
        out += f"    EarliestPacketDataEndTime: {isowithz(status['EarliestPacketDataEndTime'])}\n"
        out += f"    LatestPacketID: {status['LatestPacketID']}\n"
        out += f"    LatestPacketCreationTime: {isowithz(status['LatestPacketCreationTime'])}\n"
        out += f"    LatestPacketDataStartTime: {isowithz(status['LatestPacketDataStartTime'])}\n"
        out += f"    LatestPacketDataEndTime: {isowithz(status['LatestPacketDataEndTime'])}\n"
    if INFO_STREAMLIST in info:
        streaminfo = info[INFO_STREAMLIST]
        out +=  "  Streams:\n"
        out += f"    TotalStreams: {streaminfo['TotalStreams']}\n"
        out += f"    SelectedStreams: {streaminfo['SelectedStreams']}\n"
        streamlist = streaminfo[INFO_STREAM]
        for st in streamlist:
            out += f"    {st['Name']} latency: {st['DataLatency']}\n"
            out += f"      {st['EarliestPacketID']}  {isowithz(st['EarliestPacketDataStartTime'])}  {isowithz(st['EarliestPacketDataEndTime'])}\n"
            out += f"      {st['LatestPacketID']}  {isowithz(st['LatestPacketDataStartTime'])}  {isowithz(st['LatestPacketDataEndTime'])}\n"
    return out


def encodeAuthToken(user_id, expireDelta, writePattern, secretKey):
    """
    Note token auth is not part of ringserver proper, uses a fork I created.

    Generates a ringserver Auth Token
    user_id: user name
    expireDelta: lifetime of token, ex timedelta(days=1, seconds=60)
    writePattern: streamid reg exp, ex 'XX_.*/MTRIG'
    secretKey: encryption pass phrase, should be > 32, longer is ok
    :return: string, base64 encoded signed jwt token
    """
    payload = {
        "exp": utcnowWithTz() + expireDelta,
        "iat": utcnowWithTz(),
        "sub": user_id,
        "wpat": writePattern,
    }
    encoded = jwt.encode(payload, secretKey, algorithm="HS256")
    return encoded


def decodeAuthToken(encodedToken, secretKey):
    """
    Note token auth is not part of ringserver proper, uses a fork I created.
    """
    return jwt.decode(encodedToken, secretKey, algotithms="HS256")


def timeUntilExpireToken(token):
    """
    Note token auth is not part of ringserver proper, uses a fork I created.
    """
    payload = jwt.decode(token, verify=False)
    return datetime.fromtimestamp(payload["exp"], timezone.utc) - utcnowWithTz()
