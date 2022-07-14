import json
from datetime import datetime


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            s = obj.isoformat(sep="T")
            if s.endswith("+00:00"):
                return s[:-6] + "Z"
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
