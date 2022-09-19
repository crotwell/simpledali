

"""
Philip Crotwell
University of South Carolina, 2022
http://www.seis.sc.edu
"""

from typing import Union, Optional

FDSN_PREFIX = "FDSN:"

SEP = "_"

class FDSNSourceId:
  networkCode: str
  stationCode: str
  locationCode: str
  bandCode: str
  sourceCode: str
  subsourceCode: str
  def __init__(self,
               networkCode: str,
              stationCode: str,
              locationCode: str,
              bandCode: str,
              sourceCode: str,
              subsourceCode: str):
    self.networkCode = networkCode
    self.stationCode = stationCode
    self.locationCode = locationCode
    self.bandCode = bandCode
    self.sourceCode = sourceCode
    self.subsourceCode = subsourceCode


  @staticmethod
  def createUnknown(sampRate: Optional[Union[float , int ]] = None) -> 'FDSNSourceId':
    return FDSNSourceId("XX", "ABC", "", bandCodeForRate(sampRate), "Y", "X")

  @staticmethod
  def parse(id: str) -> Union['FDSNSourceId','NetworkSourceId','StationSourceId']:
    if (not id.startswith(FDSN_PREFIX)):
      raise FDSNSourceIdException (f"sourceid must start with {FDSN_PREFIX}: {id}")

    items = id[len(FDSN_PREFIX):].split(SEP)
    if (len(items) == 1):
        return NetworkSourceId(items[0])
    elif len(items) == 2:
        return StationSourceId(items[0], items[1])
    elif (len(items) != 6):
      raise FDSNSourceIdException (f"FDSN sourceid must have 6 items for channel, 2 for station or 1 for network; separated by '{SEP}': {id}")

    return FDSNSourceId(items[0],items[1],items[2],items[3],items[4],items[5])

  @staticmethod
  def  fromNslc(net: str, sta: str, loc: str, channelCode: str) -> 'FDSNSourceId':
    if (len(channelCode) == 3):
      band = channelCode[0]
      source = channelCode[1]
      subsource = channelCode[2]
    else:
      b_s_ss = r'(\w)_(\w+)_(\w+)'
      match = regex.match(b_s_ss, channelCode)
      if (match):
        band = match[1]
        source = match[2]
        subsource = match[3]
      else:
        raise FDSNSourceIdException (f"channel code must be length 3 or have 3 items separated by '{SEP}': {channelCode}")


    return FDSNSourceId(net, sta, loc,band,source,subsource)

  @staticmethod
  def parseNslc(nslc: str, sep = '.') -> 'FDSNSourceId':
    items = nslc.split(sep)
    if (len(items) < 4):
      raise FDSNSourceIdException (f"channel nslc must have 4 items separated by '{sep}': {nslc}")

    return FDSNSourceId.fromNslc(items[0],items[1],items[2],items[3])

  def stationSourceId(self) -> 'StationSourceId':
    return  StationSourceId(self.networkCode, self.stationCode)

  def networkSourceId(self) -> 'NetworkSourceId':
    return  NetworkSourceId(self.networkCode)

  def asNslc(self):
    if (len(self.bandCode) == 1 and len(self.sourceCode) == 1 and len(self.subsourceCode) == 1):
      chanCode = f"{self.bandCode}{self.sourceCode}{self.subsourceCode}"
    else:
      chanCode = f"{self.bandCode}{SEP}{self.sourceCode}{SEP}{self.subsourceCode}"

    return  NslcId(self.networkCode, self.stationCode, self.locationCode, chanCode)

  def __str__(self) -> str:
    return f"{FDSN_PREFIX}{self.networkCode}{SEP}{self.stationCode}{SEP}{self.locationCode}{SEP}{self.bandCode}{SEP}{self.sourceCode}{SEP}{self.subsourceCode}"

  def __eq__(self, other: Optional['FDSNSourceId'] = None) -> bool:
    if not isinstance(other, self.__class__):
        return False
    return str(self) == str(other)



class NetworkSourceId:
  networkCode: str
  def __init__(self, networkCode: str):
    self.networkCode = networkCode

  def __str__(self) -> str:
    return f"{FDSN_PREFIX}{self.networkCode}"

  def __eq__(self, other: 'NetworkSourceId') -> bool:
    if not isinstance(other, self.__class__):
        return False
    return str(self) == str(other)


class StationSourceId:
  networkCode: str
  stationCode: str
  def __init__(self, networkCode: str, stationCode: str):
    self.networkCode = networkCode
    self.stationCode = stationCode

  def __str__(self) -> str:
    return f"{FDSN_PREFIX}{self.networkCode}{SEP}{self.stationCode}"

  def networkSourceId(self) -> 'NetworkSourceId':
    return  NetworkSourceId(self.networkCode)

  def __eq__(self, other: 'StationSourceId') -> bool:
    if not isinstance(other, self.__class__):
        return False
    return str(self) == str(other)


class LocationSourceId:
  networkCode: str
  stationCode: str
  locationCode: str
  def __init__(self, networkCode: str,
              stationCode: str,
              locationCode: str):
    self.networkCode = networkCode
    self.stationCode = stationCode
    self.locationCode = locationCode

  def __str__(self) -> str:
    return f"{FDSN_PREFIX}{self.networkCode}{SEP}{self.stationCode}{SEP}{self.locationCode}"

  def __eq__(self, other: 'LocationSourceId') -> bool:
    if not isinstance(other, self.__class__):
        return False
    return str(self) == str(other)


def bandCodeForRate(sampRate: Optional[Union[float , int ]] = None,
                    resp_lb: Optional[Union[float , int ]] = None) -> str:
  if (sampRate is None):
    return 'I'

  if (sampRate >= 5000):
    return 'J'
  elif (sampRate >= 1000 and sampRate < 5000):
    if (resp_lb is not None and resp_lb < 0.1):
      return 'F'
    return 'G'
  elif (sampRate >= 250 and sampRate < 1000):
    if (resp_lb is not None and resp_lb < 0.1):
      return 'C'
    return 'D'
  elif (sampRate >= 80 and sampRate < 250):
    if (resp_lb is not None and resp_lb < 0.1):
      return 'H'
    return 'E'
  elif (sampRate >= 10 and sampRate < 80):
    if (resp_lb is not None and resp_lb < 0.1):
      return 'B'
    return 'S'
  elif (sampRate > 1 and sampRate < 10):
    return 'M'
  elif (sampRate > 0.5 and sampRate < 1.5):
    # spec not clear about how far from 1 is L
    return 'L'
  elif (sampRate >= 0.1 and sampRate < 1):
    return 'V'
  elif (sampRate >= 0.01 and sampRate < 0.1):
    return 'U'
  elif (sampRate >= 0.001 and sampRate < 0.01):
    return 'W'
  elif (sampRate >= 0.0001 and sampRate < 0.001):
    return 'R'
  elif (sampRate >= 0.00001 and sampRate < 0.0001):
    return 'P'
  elif (sampRate >= 0.000001 and sampRate < 0.00001):
    return 'T'
  elif (sampRate < 0.000001):
    return 'Q'
  else:
    raise FDSNSourceIdException (f"Unable to calc band code for: {sampRate} {resp_lb}")



class NslcId:
  networkCode: str
  stationCode: str
  locationCode: str
  channelCode: str
  def __init__(self, net: str, sta: str, loc: str, chan: str):
    self.networkCode = net
    self.stationCode = sta
    self.locationCode = loc
    self.channelCode = chan

class FDSNSourceIdException(Exception):
    pass

def main():
    import sys
    for a in sys.argv[1:]:
        sid = FDSNSourceId.parse(a)
        print(f"      {sid}")
        print(f"       Net: {sid.networkCode}")
        print(f"       Sta: {sid.stationCode}")
        print(f"       Loc: {sid.locationCode}")
        print(f"      Band: {sid.bandCode}")
        print(f"    Source: {sid.sourceCode}")
        print(f" Subsource: {sid.subsourceCode}")

if __name__ == "__main__":
    main()
