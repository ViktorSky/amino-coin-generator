#   by ReYeS
#     _;)  ~~8:> ~~8:>
#   Update by V¡ktor

parameters = {

    "community-link":
        "http://aminoapps.com/invite/5G0A09Y6RE",
    "proxies": {
        "https": "159.197.250.171:3128",
    }
}


###################
emailFile = "acc.json"
###################

import os
import time
import json
import datetime
from threading import Thread
from base64 import b64encode
from uuid import uuid4
from hashlib import sha1
from hmac import new

try:
    from websocket import (
        WebSocketConnectionClosedException as ConectionError,
        WebSocketApp
    )
    import pytz
    import requests
    from flask import Flask
    from json_minify import json_minify
except:
    os.system("pip install -r requirements.txt")
finally:
    from websocket import (
        WebSocketConnectionClosedException as ConectionError,
        WebSocketApp
    )
    import requests
    import random
    import pytz
    from flask import Flask
    from json_minify import json_minify


#-----------------FLASK-APP-----------------
flask_app = Flask('')
@flask_app.route('/')
def home(): return "~~8;> ~~8;>"
ht = '0.0.0.0'
pt = random.randint(2000, 9000)
def run():
    flask_app.run(host=ht, port=pt)
#----------------------------------------------------




class Client:
    def __init__(self, deviceId=None, proxies: dict=None) -> None:
        self.api = "https://service.narvii.com/api/v1"
        self.device_Id = self.generate_device_Id() if not deviceId else deviceId
        self.session = requests.Session()
        self.headers = {
    "NDCDEVICEID": self.device_Id,
    "SMDEVICEID":
        "b89d9a00-f78e-46a3-bd54-6507d68b343c",
    "Accept-Language": "en-EN",
    "Content-Type":
        "application/json; charset=utf-8",
    "User-Agent":
        "Dalvik/2.1.0 (Linux; U; Android 5.1.1; SM-G973N Build/beyond1qlteue-user 5; com.narvii.amino.master/3.4.33562)",
    "Host": "service.narvii.com",
    "Accept-Encoding": "gzip",
    "Connection": "Keep-Alive"}
        self.proxies = proxies
        self.socket_thread, self.sid = None, None
        self.socket, self.auid = None, None

    def generate_signature_message(self, data: str) -> str:
        signature_message = b64encode(bytes.fromhex("42") + new(bytes.fromhex("F8E7A61AC3F725941E3AC7CAE2D688BE97F30B93"),data.encode("utf-8"), sha1).digest()).decode("utf-8")
        self.headers["NDC-MSG-SIG"]=signature_message
        return signature_message

    def generate_device_Id(self) -> str:
        identifier = os.urandom(20)
        mac = new(bytes.fromhex("02B258C63559D8804321C5D5065AF320358D366F"), bytes.fromhex("42") + identifier, sha1)
        return f"42{identifier.hex()}{mac.hexdigest()}".upper()
    
    def ws_send(self, data):
        if self.sid is None: return
        final = f"{self.device_Id}|{int(time.time() * 1000)}"
        ndc_msg_sig = self.generate_signature_message(final)
        headers = {
            "NDCDEVICEID": self.device_Id,
            "NDCAUTH": f"sid={self.sid}",
            "NDC-MSG-SIG": ndc_msg_sig
        }
        
        host, port = None, None
        
        if any(self.proxies) and (proxy:=self.proxies.get("http")):
            host = proxy[::-1][proxy[::-1].index(":")+1:][::-1]
            port = int(proxy[::-1][:proxy[::-1].index(":")][::-1])
        
        for n in range(4, 0, -1):
            try:
                self.socket = WebSocketApp(
                    "wss://ws%d.narvii.com/?signbody=%s" % (
                        n, final.replace('|', '%7C')
                    ),
                    header=headers
                )
                self.socket_thread = Thread(
                    target=self.socket.run_forever,
                    kwargs={"http_proxy_host": host,
                    "http_proxy_port": port}
                )
                self.socket_thread.start()
                time.sleep(3)
                return self.socket.send(data)
            except (ConectionError) as Error:
                print(Error)
                continue

    def login(self, email: str, password: str):
        data = json.dumps({
             "email": email,
             "secret": f"0 {password}",
             "deviceID": self.device_Id,
             "clientType": 100,
             "action": "normal",
             "timestamp": (int(time.time() * 1000))})
        self.generate_signature_message(data = data)
        request = self.session.post(f"{self.api}/g/s/auth/login", data=data, headers=self.headers, proxies=self.proxies).json()
        try:
            self.sid = request["sid"]
            self.auid = request["auid"]
        except: pass
        return request

    def join_community(self, comId: int, inviteId: str = None):
        data = {"timestamp": int(time.time() * 1000)}
        if inviteId: data["invitationId"] = inviteId
        data = json.dumps(data)
        self.generate_signature_message(data=data)
        request = self.session.post(f"{self.api}/x{comId}/s/community/join?sid={self.sid}", data=data, headers=self.headers, proxies=self.proxies).json()
        return request

    def send_active_object(self, comId: int, timers: list=None, tz: int = -time.timezone // 1000):
        data = {
            "userActiveTimeChunkList": timers,
            "timestamp": int(time.time() * 1000),
            "optInAdsFlags": 2147483647,
            "timezone": tz
            }
        data = json_minify(json.dumps(data))
        self.generate_signature_message(data = data)
        request = self.session.post(f"{self.api}/x{comId}/s/community/stats/user-active-time?sid={self.sid}", data=data, headers=self.headers, proxies=self.proxies).json()
        return request

    def watch_ad(self):
        return self.session.post(f"{self.api}/g/s/wallet/ads/video/start?sid={self.sid}", headers=self.headers, proxies=self.proxies).json()

    def get_from_link(self, link: str):
        return self.session.get(f"{self.api}/g/s/link-resolution?q={link}", headers=self.headers, proxies=self.proxies).json()

    def lottery(self, comId, time_zone: str = -int(time.timezone) // 1000):
        data = json.dumps({
            "timezone": time_zone,
            "timestamp": int(time.time() * 1000)})
        self.generate_signature_message(data = data)
        request = self.session.post(f"{self.api}/x{comId}/s/check-in/lottery?sid={self.sid}", data=data, headers=self.headers, proxies=self.proxies).json()
        return request
    
    def show_online(self, comId):
        data = {"o": {
            "actions": ["Browsing"],
            "target": f"ndc://x{comId}/",
            "ndcId": int(comId),
            "id": "82333"}, "t":304}
        data = json.dumps(data)
        time.sleep(1)
        self.ws_send(data)

class Config:
    def __init__(self):
        with open(emailFile, "r") as config:
            self.account_list = [d for d in json.load(config)]

class App:
    def __init__(self):
        self.proxies = parameters["proxies"]
        self.client = Client(proxies=self.proxies)
        extensions = self.client.get_from_link(parameters["community-link"])["linkInfoV2"]["extensions"]
        self.comId=extensions["community"]["ndcId"]
        try: self.invitationId = extensions["invitationId"]
        except: self.invitationId = None

    def tzc(self) -> int:
        tz = dict(zip(("GMT" if i==0 else f'{"+"if i>0 else "-"}{"0"if -10<i<10 else ""}{i*-1 if i<0 else i}' for i in range(-12,12)),(i*60 for i in range(-12,12))))
        zones = ['Etc/GMT-11','Etc/GMT-10','Etc/GMT-9','Etc/GMT-8','Etc/GMT-7','Etc/GMT-6','Etc/GMT-5','Etc/GMT-4','Etc/GMT-3','Etc/GMT-2','Etc/GMT-1','Etc/GMT0','Etc/GMT+1','Etc/GMT+2','Etc/GMT+3','Etc/GMT+4','Etc/GMT+5','Etc/GMT+6','Etc/GMT+7','Etc/GMT+8','Etc/GMT+9','Etc/GMT+10','Etc/GMT+11','Etc/GMT+12']
        for _ in zones:
            H = datetime.datetime.now(pytz.timezone(_)).strftime("%H")
            Z = datetime.datetime.now(pytz.timezone(_)).strftime("%Z")
            if H=="23": break
        timezone = tz.get(Z)
        return timezone

    def generation(self, email: str, password: str, device: str) -> None:
        self.email,self.password = email, password
        self.client = Client(device, proxies=self.proxies)
        try:
            print(f"\n[\033[1;31mcoins-generator\033[0m][\033[1;34mlogin\033[0m][{email}]: {self.client.login(email = self.email, password = self.password)['api:message']}.")
            print(f"[\033[1;31mcoins-generator\033[0m][\033[1;36mjoin-community\033[0m]: {self.client.join_community(comId = self.comId, inviteId = self.invitationId)['api:message']}.")
            self.client.show_online(self.comId)
            print(f"[\033[1;31mcoins-generator\033[0m][\033[1;32mlottery\033[0m]: {self.client.lottery(comId = self.comId, time_zone = self.tzc())['api:message']}")
            print(f"[\033[1;31mcoins-generator\033[0m][\033[1;33mwatch-ad\033[0m]: {self.client.watch_ad()['api:message']}.")
            for i2 in range(24): print(f"[\033[1;31mcoins-generator\033[0m][\033[1;35mmain-proccess\033[0m][{email}]: {self.client.send_active_object(comId = self.comId, timers = [{'start': int(time.time()), 'end': int(time.time()) + 300} for _ in range(50)], tz = self.tzc())['api:message']}."); time.sleep(4)
            print(f"[\033[1;31mcoins-generator\033[0m][\033[1;25;32mend\033[0m][{email}]: Finished.")
        except Exception as error: print(f"[\033[1;31mC01?-G3?3R4?0R\033[0m]][\033[1;31merror\033[0m]]: {error}")

    def run(self):
        print("\033[1;31m @@@@@@   @@@@@@@@@@   @@@  @@@  @@@   @@@@@@ \033[0m     \033[1;32m @@@@@@@   @@@@@@   @@@  @@@  @@@   @@@@@@\033[0m\n\033[1;31m@@@@@@@@  @@@@@@@@@@@  @@@  @@@@ @@@  @@@@@@@@\033[0m     \033[1;32m@@@@@@@@  @@@@@@@@  @@@  @@@@ @@@  @@@@@@@\033[0m\n\033[1;31m@@!  @@@  @@! @@! @@!  @@!  @@!@!@@@  @@!  @@@\033[0m     \033[1;32m!@@       @@!  @@@  @@!  @@!@!@@@  !@@\033[0m\n\033[1;31m!@!  @!@  !@! !@! !@!  !@!  !@!!@!@!  !@!  @!@\033[0m     \033[1;32m!@!       !@!  @!@  !@!  !@!!@!@!  !@!\033[0m\n\033[1;31m@!@!@!@!  @!! !!@ @!@  !!@  @!@ !!@!  @!@  !@!\033[0m     \033[1;32m!@!       @!@  !@!  !!@  @!@ !!@!  !!@@!!\033[0m\n\033[1;31m!!!@!!!!  !@!   ! !@!  !!!  !@!  !!!  !@!  !!!\033[0m     \033[1;32m!!!       !@!  !!!  !!!  !@!  !!!   !!@!!!\033[0m\n\033[1;31m!!:  !!!  !!:     !!:  !!:  !!:  !!!  !!:  !!!\033[0m     \033[1;32m:!!       !!:  !!!  !!:  !!:  !!!       !:!\033[0m\n\033[1;31m:!:  !:!  :!:     :!:  :!:  :!:  !:!  :!:  !:!\033[0m     \033[1;32m:!:       :!:  !:!  :!:  :!:  !:!      !:!\033[0m\n\033[1;31m::   :::  :::     ::    ::   ::   ::  ::::: ::\033[0m     \033[1;32m ::: :::  ::::: ::   ::   ::   ::  :::: ::\033[0m\n\033[1;31m :   : :   :      :    :    ::    :    : :  : \033[0m     \033[1;32m :: :: :   : :  :   :    ::    :   :: : :\033[0m\n\033[1;33m @@@@@@@@  @@@@@@@@  @@@  @@@  @@@@@@@@  @@@@@@@    @@@@@@   @@@@@@@   @@@@@@   @@@@@@@\033[0m\n\033[1;33m@@@@@@@@@  @@@@@@@@  @@@@ @@@  @@@@@@@@  @@@@@@@@  @@@@@@@@  @@@@@@@  @@@@@@@@  @@@@@@@@\033[0m\n\033[1;33m!@@        @@!       @@!@!@@@  @@!       @@!  @@@  @@!  @@@    @@!    @@!  @@@  @@!  @@@\033[0m\n\033[1;33m!@!        !@!       !@!!@!@!  !@!       !@!  @!@  !@!  @!@    !@!    !@!  @!@  !@!  @!@\033[0m\n\033[1;33m!@! @!@!@  @!!!:!    @!@ !!@!  @!!!:!    @!@!!@!   @!@!@!@!    @!!    @!@  !@!  @!@!!@!\033[0m\n\033[1;33m!!! !!@!!  !!!!!:    !@!  !!!  !!!!!:    !!@!@!    !!!@!!!!    !!!    !@!  !!!  !!@!@!\033[0m\n\033[1;33m:!!   !!:  !!:       !!:  !!!  !!:       !!: :!!   !!:  !!!    !!:    !!:  !!!  !!: :!!\033[0m\n\033[1;33m:!:   !::  :!:       :!:  !:!  :!:       :!:  !:!  :!:  !:!    :!:    :!:  !:!  :!:  !:!\033[0m\n\033[1;33m ::: ::::   :: ::::   ::   ::   :: ::::  ::   :::  ::   :::     ::    ::::: ::  ::   :::\033[0m\n\033[1;33m :: :: :   : :: ::   ::    :   : :: ::    :   : :   :   : :     :      : :  :    :   : :\033[0m\n\033[1;35m__By ReYeS\033[0m / \033[1;36mREPLIT_EDITION\033[0m\n")
        while True:
            for acc in Config().account_list:
                e = acc['email']
                p = acc['password']
                d = acc['device']
                self.generation(e, p, d)

if __name__ == "__main__":
    Thread(target=run).start()
    App().run()
