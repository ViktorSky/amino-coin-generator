#  by ReYeS
#    _;)  ~~8:> ~~8:>
#  Update by V¡ktor
#  https://github.com/ViktorSky/amino-coin-generator

import os
import time
import json
from datetime import datetime
from random import randint
from threading import Thread
from base64 import b64encode
from hashlib import sha1
from hmac import new

os.system('pip install -r requirements.txt')

from websocket import WebSocketApp, WebSocketConnectionClosedException
from requests import Session
from yarl import URL
import pytz
from flask import Flask
from json_minify import json_minify


parameters = {
    "community-link":
        "http://aminoapps.com/invite/77FC1LEDHT",
    "accounts-file":
        "acc.json",
    "proxies": {
        "https": None
    }
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
    api = "https://service.aminoapps.com/api/v1"

    def __init__(self, device=None, proxies=None) -> None:
        self.device = device or self.generate_device()
        self.proxies = proxies or {}
        self.session = Session()
        self.socket = None
        self.socket_thread = None
        self.sid = None
        self.auid = None

    def build_headers(self, data=None):
        headers = {
            "NDCDEVICEID": self.device,
            "SMDEVICEID": "b89d9a00-f78e-46a3-bd54-6507d68b343c",
            "Accept-Language": "en-EN",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "User-Agent": "Apple iPhone12,1 iOS v15.5 Main/3.12.2",
            "Host": "service.narvii.com",
            "Accept-Encoding": "gzip",
            "Connection": "Keep-Alive"
        }
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

    def generate_device(self):
        info = bytes.fromhex(PREFIX) + os.urandom(20)
        return info.hex() + new(
            bytes.fromhex(DEVKEY),
            info, sha1
        ).hexdigest()

    def ws_send(self, data):
        if self.sid is None:
            return
        final = f"%s|%d" % (self.device, int(time.time() * 1000))
        kwargs = {}
        proxy = self.proxies.get('https')
        if proxy:
            url = URL(f"https://{proxy}" if "http" not in proxy else proxy)
            kwargs["proxy_type"] = url.scheme if 'http' in url.scheme else 'https'
            kwargs["http_proxy_host"] = url.host
            kwargs["http_proxy_port"] = url.port
            if url.user:
                kwargs["http_proxy_auth"] = (url.user, url.password)
        socket_url = URL("wss://ws%d.aminoapps.com/?signbody=%s")
        if not kwargs.get("proxy_type", "https").endswith("s"):
            socket_url = socket_url.with_scheme("ws")
        for n in range(4, 0, -1):
            try:
                self.socket = WebSocketApp(
                    socket_url.human_repr() % (n, final.replace('|', '%7C')),
                    header=self.build_headers(final)
                )
                self.socket_thread = Thread(
                    target=self.socket.run_forever,
                    kwargs=kwargs
                )
                self.socket_thread.start()
                time.sleep(3.2)
                return self.socket.send(data)
            except WebSocketConnectionClosedException:
                continue

    def login(self, email, password):
        data = json.dumps({
             "email": email,
             "secret": "0 %s" % password,
             "deviceID": self.device,
             "clientType": 100,
             "action": "normal",
             "timestamp": int(time.time() * 1000)
        })
        request = self.session.post(
            url="%s/g/s/auth/login" % self.api,
            data=data,
            headers=self.build_headers(data),
            proxies=self.proxies
        ).json()
        self.sid = request.get("sid")
        self.auid = request.get("auid")
        return request

    def join_community(self, ndcId, invitationId=None):
        data = {"timestamp": int(time.time() * 1000)}
        if invitationId:
            data["invitationId"] = invitationId
        data = json.dumps(data)
        return self.session.post(
            url="%s/x%s/s/community/join?sid=%s&auid=%s" % (self.api, ndcId, self.sid, self.auid),
            data=data,
            headers=self.build_headers(data),
            proxies=self.proxies
        ).json()

    def send_active_object(self, ndcId, timers=None, timezone=0):
        data = json_minify(json.dumps({
            "userActiveTimeChunkList": timers,
            "timestamp": int(time.time() * 1000),
            "optInAdsFlags": 2147483647,
            "timezone": timezone
        }))
        return self.session.post(
            url="%s/x%s/s/community/stats/user-active-time?sid=%s&auid=%s" % (self.api, ndcId, self.sid, self.auid),
            data=data,
            headers=self.build_headers(data),
            proxies=self.proxies
        ).json()

    def watch_ad(self):
        return self.session.post(
            "%s/g/s/wallet/ads/video/start?sid=%s&auid=%s" % (self.api, self.sid, self.auid),
            headers=self.build_headers(),
            proxies=self.proxies
        ).json()

    
    def get_from_link(self, link):
        return self.session.get(
            url="%s/g/s/link-resolution?q=%s" % (self.api, link),
            headers=self.build_headers(),
            proxies=self.proxies
        ).json()

    def lottery(self, ndcId, timezone=0):
        data = json.dumps({
            "timezone": timezone,
            "timestamp": int(time.time() * 1000)
        })
        return self.session.post(
            url="%s/x%s/s/check-in/lottery?sid=%s&auid=%s" % (self.api, ndcId, self.sid, self.auid),
            data=data,
            headers=self.build_headers(data),
            proxies=self.proxies
        ).json()

    def show_online(self, ndcId):
        self.ws_send(json.dumps({
            "o": {
                "actions": ["Browsing"],
                "target": "ndc://x%s/" % ndcId,
                "ndcId": int(ndcId),
                "id": "82333"
            },
            "t": 304
        }))


class Config:
    def __init__(self):
        with open(parameters["accounts-file"], "r") as config:
            self.account_list = json.load(config)


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
            zone = datetime.now(pytz.timezone(_))
            if zone.hour != 23:
                continue
            return int(zone.strftime('%Z').replace('GMT', '00')) * 60
        return 0

    def generation(self, email, password, device):
        if device:
            self.client.device = device
        start = time.time()
        try:
            message = self.client.login(email, password)['api:message']
            print("\n[\033[1;31mcoins-generator\033[0m][\033[1;34mlogin\033[0m][%s]: %s." % (email, message))
            message = self.client.join_community(self.ndcId, self.invitationId)['api:message']
            print("[\033[1;31mcoins-generator\033[0m][\033[1;36mjoin-community\033[0m]: %s." % message)
            self.client.show_online(self.ndcId)
            message = self.client.lottery(self.ndcId, self.tzc())['api:message']
            print("[\033[1;31mcoins-generator\033[0m][\033[1;32mlottery\033[0m]: %s" % message)
            message = self.client.watch_ad()['api:message']
            print("[\033[1;31mcoins-generator\033[0m][\033[1;33mwatch-ad\033[0m]: %s." % message)
            for _ in range(24):
                timers = [{'start': int(time.time()), 'end': int(time.time()) + 300} for _ in range(50)]
                message = self.client.send_active_object(self.ndcId, timers, self.tzc())['api:message']
                print("[\033[1;31mcoins-generator\033[0m][\033[1;35mmain-proccess\033[0m][%s]: %s." % (email, message))
                time.sleep(4)
            end = int(time.time() - start)
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
