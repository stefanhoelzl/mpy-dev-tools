import json
import http.client


from .base_device import BaseDevice


class ApifyRepl(BaseDevice):
    def __init__(self, ip_with_port):
        ip, port = ip_with_port.split(":")
        self.ip = ip
        self.port = port

    def connect(self):
        pass

    def flush(self):
        pass

    def enter_raw_repl(self):
        pass

    def close(self):
        pass

    def run_cmd(self, command, mode):
        print("({}) {}".format(mode, command))
        connection = http.client.HTTPConnection(self.ip, self.port)
        connection.request("POST", "/repl/{}".format(mode),
                                body=json.dumps(command))
        resp = connection.getresponse().read()
        connection.close()
        v = json.loads(resp.decode("ascii"))
        if isinstance(v, list):
            return str(tuple(v))
        else:
            return str(v)

    def exec(self, command, output=None):
        return self.run_cmd(command, mode="exec")

    def eval(self, expression, output=None):
        return self.run_cmd(expression, mode="eval")
