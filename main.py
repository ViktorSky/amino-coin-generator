#  by ReYeS
#    _;)  ~~8:> ~~8:>
#  updated by V¡ktor
#  v3.0.0
#  https://github.com/ViktorSky/amino-coin-generator

import os
from urllib.parse import urljoin, urlencode
from time import time, sleep
from json import dumps, load
from datetime import datetime
from random import randint
from threading import Thread
from base64 import b64encode
from hashlib import sha1
from hmac import new

os.system('pip install -r requirements.txt')

from websocket import WebSocket, WebSocketConnectionClosedException
from requests import Session
from yarl import URL
from pytz import timezone as pytz_timezone
from flask import Flask
from json_minify import json_minify


parameters = {
    # community link or invite link
    "community-link":
        "http://aminoapps.com/invite/77FC1LEDHT",
    # file containing the accounts list[dict]: email, password, device
    "accounts-file":
        "acc.json",
    # proxy for https and wss requests
    "proxies": {
        "https": None
    },
    # header content-language: english: 'en-US', spanish: 'es-ES', ...
    "logger-language": "en-US",
    # send-activity cooldown
    "activity-coldown": 5,
    # api requests cooldown
    "request-cooldown": 1,
    # browse bots in the community (online)
    "show-online": True,
}

PREFIX = '19'
DEVKEY = 'e7309ecc0953c6fa60005b2765f99dbbc965c8e9'
SIGKEY = 'dfa5ed192dda6e88a12fe12130dc6206b1251e44'

# -----------------FLASK-APP-----------------
flask_app = Flask('amino-coin-generator')
@flask_app.route('/')
def home():
    return "~~8;> ~~8;>"

def run():
    flask_app.run('0.0.0.0', randint(2000, 9000))
# -------------------------------------------


class Client:
    api = "https://service.aminoapps.com/api/v1/"

    def __init__(self, device=None, proxies=None) -> None:
        self.device = self.update_device(device or self.generate_device())
        self.proxies = proxies or {}
        self.session = Session()
        self.socket = WebSocket()
        self.socket_thread = None
        self.sid = None
        self.auid = None

    @property
    def connected(self):
        return isinstance(self.socket, WebSocket) and self.socket.connected

    def build_headers(self, data=None, content_type=None):
        headers = {
            "NDCDEVICEID": self.device,
            "SMDEVICEID": "b89d9a00-f78e-46a3-bd54-6507d68b343c",
            "Accept-Language": parameters.get('logger-language', 'en-US'),
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "User-Agent": "Apple iPhone12,1 iOS v15.5 Main/3.12.2",
            "Host": "service.aminoapps.com",
            "Accept-Encoding": "gzip",
            "Connection": "Keep-Alive"
        }
        if content_type:
            headers["Content-Type"] = content_type
        if data:
            headers["NDC-MSG-SIG"] = self.generate_signature(data)
        if self.sid:
            headers["NDCAUTH"] = "sid=%s" % self.sid
        if self.auid:
            headers["AUID"] = self.auid
        return headers

    def generate_signature(self, data):
        return b64encode(
            bytes.fromhex(PREFIX) + new(
                bytes.fromhex(SIGKEY),
                data.encode("utf-8"),
                sha1
            ).digest()
        ).decode("utf-8")

    def generate_device(self, info=None):
        data = bytes.fromhex(PREFIX) + (info or os.urandom(20))
        return data.hex() + new(
            bytes.fromhex(DEVKEY),
            data, sha1
        ).hexdigest()

    def update_device(self, device):
        return self.generate_device(bytes.fromhex(device)[1:21])

    def ws_connect(self):
        if not self.sid:
            return
        final = f"%s|%d" % (self.device, int(time() * 1000))
        kwargs, header = {}, {
            'NDCDEVICEID': self.device,
            'NDCAUTH': self.sid,
            'Content-Type': 'text/plain',
            'NDC-MSG-SIG': self.generate_signature(final)
        }
        proxy = self.proxies.get('https')
        if proxy:
            url = URL(f"https://{proxy}" if "://" not in proxy else proxy)
            kwargs["proxy_type"] = url.scheme
            kwargs["http_proxy_host"] = url.host
            kwargs["http_proxy_port"] = url.port
            if url.user:
                kwargs["http_proxy_auth"] = (url.user, url.password)
        socket_url = URL("wss://ws%d.aminoapps.com/?signbody=%s")
        if not kwargs.get("proxy_type", "https").endswith(("s", "5")):
            socket_url = socket_url.with_scheme("ws")
        for n in range(4, 0, -1):
            try:
                connect_url = socket_url.human_repr() % (n, final.replace('|', '%7C'))
                self.socket.connect(url=connect_url, header=header, **kwargs)
            except WebSocketConnectionClosedException:
                sleep(1)
                continue
            else:
                break

    def ws_send(self, data):
        if not self.connected:
            return
        self.socket.send(data)

    def request(self, method, path, json, minify=False, ndcId=0, scope=False):
        ndc = (f'g/s-x{ndcId}/' if scope else f'x{ndcId}/s/') if ndcId else 'g/s/'
        url = urljoin(self.api, urljoin(ndc, path.removeprefix('/')))
        data, method = None, method.upper()
        if method in ['GET'] and json:
            if not url.count('?'):
                url += '?'
            url += urlencode(json)
        elif method in ['POST']:
            data = dumps(json or {})
            if minify:
                data = json_minify(data)
        else:
            raise NotImplementedError(method)
        headers = self.build_headers(data)
        return self.session.request(
            method=method,
            url=url,
            data=data,
            headers=headers,
            proxies=self.proxies
        ).json()

    def login(self, email, password):
        response = self.request('POST', 'auth/login', {
             "email": email,
             "secret": "0 %s" % password,
             "deviceID": self.device,
             "clientType": 100,
             "action": "normal",
             "timestamp": int(time() * 1000)
        })
        self.sid = response.get("sid")
        self.auid = response.get("auid")
        return response

    def join_community(self, ndcId, invitationId=None):
        data = {"timestamp": int(time() * 1000)}
        if invitationId:
            data["invitationId"] = invitationId
        return self.request('POST', f'community/join?sid={self.sid}&auid={self.auid}', data, ndcId=ndcId)

    def send_active_object(self, ndcId, timers=None, timezone=0):
        return self.request('POST', f'community/stats/user-active-time?sid={self.sid}&auid={self.auid}', {
            "userActiveTimeChunkList": timers,
            "timestamp": int(time() * 1000),
            "optInAdsFlags": 2147483647,
            "timezone": timezone
        }, minify=True, ndcId=ndcId)

    def watch_ad(self):
        return self.request('POST', f'wallet/ads/video/start?sid={self.sid}&auid={self.auid}', {
            'timestamp': int(time() * 1000)
        })
    
    def get_from_link(self, link):
        return self.request('GET', 'link-resolution', {'q': link})

    def lottery(self, ndcId, timezone=0):
        return self.request('POST', f'check-in/lottery?sid={self.sid}&auid={self.auid}', {
            "timezone": timezone,
            "timestamp": int(time() * 1000)
        }, ndcId=ndcId)

    def show_online(self, ndcId):
        self.ws_send(dumps({
            "o": {
                "actions": ["Browsing"],
                "target": "ndc://x%s/" % ndcId,
                "ndcId": ndcId,
                "id": "82333"
            },
            "t": 304
        }))


class Config:
    def __init__(self):
        with open(parameters["accounts-file"], "r") as config:
            self.account_list = load(config)


class App:
    def __init__(self):
        self.proxies = parameters["proxies"]
        self.client = Client(proxies=self.proxies)
        info = self.client.get_from_link(parameters["community-link"])
        try: extensions = info["linkInfoV2"]["extensions"]
        except KeyError:
            raise RuntimeError('community: %s' % info["api:message"])
        self.ndcId = extensions["community"]["ndcId"]
        self.invitationId = extensions.get("invitationId")

    def tzc(self):
        for _ in ['Etc/GMT' + (f'+{i}' if i > 0 else str(i)) for i in range(-12, 12)]:
            zone = datetime.now(pytz_timezone(_))
            if zone.hour != 23:
                continue
            return int(zone.strftime('%Z').replace('GMT', '00')) * 60
        return 0

    def generation(self, email, password, device):
        if device:
            self.client.device = device
        start = time()
        try:
            message = self.client.login(email, password)['api:message']
            print("\n[\033[1;31mcoins-generator\033[0m][\033[1;34mlogin\033[0m][%s]: %s." % (email, message))
            sleep(parameters.get('request-cooldown', 1))
            message = self.client.join_community(self.ndcId, self.invitationId)['api:message']
            print("[\033[1;31mcoins-generator\033[0m][\033[1;36mjoin-community\033[0m]: %s." % message)
            sleep(parameters.get('request-cooldown', 1))
            if parameters.get('show-online', True):
                self.client.ws_connect()
                self.client.show_online(self.ndcId)
            message = self.client.lottery(self.ndcId, self.tzc())['api:message']
            print("[\033[1;31mcoins-generator\033[0m][\033[1;32mlottery\033[0m]: %s" % message)
            sleep(parameters.get('request-cooldown', 1))
            message = self.client.watch_ad()['api:message']
            print("[\033[1;31mcoins-generator\033[0m][\033[1;33mwatch-ad\033[0m]: %s." % message)
            sleep(parameters.get('request-cooldown', 1))
            for _ in range(24):
                timers = [{'start': int(time()), 'end': int(time()) + 300} for _ in range(50)]
                message = self.client.send_active_object(self.ndcId, timers, self.tzc())['api:message']
                print("[\033[1;31mcoins-generator\033[0m][\033[1;35mmain-proccess\033[0m][%s]: %s." % (email, message))
                sleep(parameters.get('activity-coldown', 5))
            end = int(time() - start)
            total = ("%d minutes" % round(end/60)) if end > 90 else ("%d seconds" % end)
            print("[\033[1;31mcoins-generator\033[0m][\033[1;25;32mend\033[0m]: Finished in %s." % total)
        except Exception as error:
            print("[\033[1;31mC01?-G3?3R4?0R\033[0m]][\033[1;31merror\033[0m]]: %s(%s)" % (type(error).__name__, error))

    def run(self):
        print("\033[1;31m @@@@@@   @@@@@@@@@@   @@@  @@@  @@@   @@@@@@ \033[0m     \033[1;32m @@@@@@@   @@@@@@   @@@  @@@  @@@   @@@@@@\033[0m\n\033[1;31m@@@@@@@@  @@@@@@@@@@@  @@@  @@@@ @@@  @@@@@@@@\033[0m     \033[1;32m@@@@@@@@  @@@@@@@@  @@@  @@@@ @@@  @@@@@@@\033[0m\n\033[1;31m@@!  @@@  @@! @@! @@!  @@!  @@!@!@@@  @@!  @@@\033[0m     \033[1;32m!@@       @@!  @@@  @@!  @@!@!@@@  !@@\033[0m\n\033[1;31m!@!  @!@  !@! !@! !@!  !@!  !@!!@!@!  !@!  @!@\033[0m     \033[1;32m!@!       !@!  @!@  !@!  !@!!@!@!  !@!\033[0m\n\033[1;31m@!@!@!@!  @!! !!@ @!@  !!@  @!@ !!@!  @!@  !@!\033[0m     \033[1;32m!@!       @!@  !@!  !!@  @!@ !!@!  !!@@!!\033[0m\n\033[1;31m!!!@!!!!  !@!   ! !@!  !!!  !@!  !!!  !@!  !!!\033[0m     \033[1;32m!!!       !@!  !!!  !!!  !@!  !!!   !!@!!!\033[0m\n\033[1;31m!!:  !!!  !!:     !!:  !!:  !!:  !!!  !!:  !!!\033[0m     \033[1;32m:!!       !!:  !!!  !!:  !!:  !!!       !:!\033[0m\n\033[1;31m:!:  !:!  :!:     :!:  :!:  :!:  !:!  :!:  !:!\033[0m     \033[1;32m:!:       :!:  !:!  :!:  :!:  !:!      !:!\033[0m\n\033[1;31m::   :::  :::     ::    ::   ::   ::  ::::: ::\033[0m     \033[1;32m ::: :::  ::::: ::   ::   ::   ::  :::: ::\033[0m\n\033[1;31m :   : :   :      :    :    ::    :    : :  : \033[0m     \033[1;32m :: :: :   : :  :   :    ::    :   :: : :\033[0m\n\033[1;33m @@@@@@@@  @@@@@@@@  @@@  @@@  @@@@@@@@  @@@@@@@    @@@@@@   @@@@@@@   @@@@@@   @@@@@@@\033[0m\n\033[1;33m@@@@@@@@@  @@@@@@@@  @@@@ @@@  @@@@@@@@  @@@@@@@@  @@@@@@@@  @@@@@@@  @@@@@@@@  @@@@@@@@\033[0m\n\033[1;33m!@@        @@!       @@!@!@@@  @@!       @@!  @@@  @@!  @@@    @@!    @@!  @@@  @@!  @@@\033[0m\n\033[1;33m!@!        !@!       !@!!@!@!  !@!       !@!  @!@  !@!  @!@    !@!    !@!  @!@  !@!  @!@\033[0m\n\033[1;33m!@! @!@!@  @!!!:!    @!@ !!@!  @!!!:!    @!@!!@!   @!@!@!@!    @!!    @!@  !@!  @!@!!@!\033[0m\n\033[1;33m!!! !!@!!  !!!!!:    !@!  !!!  !!!!!:    !!@!@!    !!!@!!!!    !!!    !@!  !!!  !!@!@!\033[0m\n\033[1;33m:!!   !!:  !!:       !!:  !!!  !!:       !!: :!!   !!:  !!!    !!:    !!:  !!!  !!: :!!\033[0m\n\033[1;33m:!:   !::  :!:       :!:  !:!  :!:       :!:  !:!  :!:  !:!    :!:    :!:  !:!  :!:  !:!\033[0m\n\033[1;33m ::: ::::   :: ::::   ::   ::   :: ::::  ::   :::  ::   :::     ::    ::::: ::  ::   :::\033[0m\n\033[1;33m :: :: :   : :: ::   ::    :   : :: ::    :   : :   :   : :     :      : :  :    :   : :\033[0m\n\033[1;35m__By ReYeS\033[0m / \033[1;36mREPLIT_EDITION\033[0m\n")
        while True:
            for acc in Config().account_list:
                e = acc['email']
                p = acc['password']
                d = acc['device']
                self.generation(e, p, d)

if __name__ == "__main__":
    os.system("cls" if os.name == 'nt' else "clear")
    Thread(target=run).start()
    try:
        App().run()
    except KeyboardInterrupt:
        os.abort()
