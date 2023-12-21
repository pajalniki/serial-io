class SocketioEvent():

    device_code: str
    action: str
    payload: any

    def __init__(self, device_code, action, payload):
        self.device_code = device_code
        self.action = action
        self.payload = payload