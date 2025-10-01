import pytest

# tomllib is std in python > 3.11 so do conditional import
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


from simpledali import Dali2Jsonl
from simplemseed import FDSNSourceId


class TestDali2jsonl:
    def test_tomlConfig(self):
        toml = """#comment at top for py string indent
        [datalink]
        # datalink host, defaults to localhost
        host='localhost'
        # datalink port, defaults to 16000
        port=16000
        # or via websockets, ListenPort defaults to 18000
        websocket='ws://localhost:18000/datalink'

        # Match regular expression pattern on stream ids, ex '.*/JSON'
        # if type is /BZJSON, assumes bzip2 compress of JSON data and will
        # decompress before writing to jsonl
        match='.*/(BZ)?JSON'

        [jsonl]
        # JSONL default Write pattern, usage similar to MSeedWrite in ringserver
        # %n - network
        # %s - station
        # %l - location
        # %c - channel
        # %Y - year
        # %j - day of year
        # %H - hour
        # base pattern
        write='/tmp/jsonl/%n/%s/%Y/%j/%n.%s.%l.%c.%Y.%j.%H.jsonl'

        [jsonl.bandwrite]
        # may also have separate pattern based on band code,
        # for example band W is
        # Band: W - Ultra-ultra Long Period, >= 0.001 to < 0.01 Hz
        # and so use a daily pattern instead of hourly
        W='/tmp/jsonl/%n/%s/%Y/%j/%n.%s.%l.%c.%Y.%j.jsonl'
        # also use the same pattern for U and V
        V='W'
        U='W'
        """

        conf = tomllib.loads(toml)
        d2j = Dali2Jsonl.from_config(conf)
        assert "W" in d2j.bandPatterns
        assert "U" in d2j.bandPatterns
        assert "V" in d2j.bandPatterns
        assert d2j.bandPatterns["W"] == d2j.bandPatterns["U"]
        assert d2j.bandPatterns["W"] == d2j.bandPatterns["V"]
        h_sid = FDSNSourceId.parse("FDSN:CO_BIRD_00_H_H_Z")
        
        w_sid = FDSNSourceId.parse("FDSN:CO_BIRD_00_W_K_Z")
