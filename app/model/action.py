class BaseAction:
  type: str
  payload: dict

  def __init__(self, type, payload):
    self.type = type
    self.payload = payload
