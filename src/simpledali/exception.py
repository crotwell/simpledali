


class CodecException(Exception):
  def __init__(self, message):
    super().__init__(message)
    self.message = message
    self.name = "CodecException"


class UnsupportedCompressionType(Exception):
  def __init__(self, message):
    super().__init__(message)
    self.message = message
    self.name = "UnsupportedCompressionType"
