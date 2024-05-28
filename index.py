import os
import json
import time

from httpx import Client
from websocket import WebSocketApp
from user_agent import generate_user_agent
from threading import Thread

AUTH_PAYLOAD_SENT = False
TOTAL_HEARTBEAT_SENT = 0

class Sniper(WebSocketApp):
    def __init__(self):
        self.token = ""
        self.targetGuild = ""
        self.claimGuild = ""
        self.targetVanity = ""
        
        self.websocketVersion = 7 # recommended, but you can change it as your wish
        self.session = self.createSession()
        
        self.address = f"wss://gateway.discord.gg/?v={self.websocketVersion}&encoding=json"
        self.heartbeatInterval = None # do not touch it just because its a none type object, it will be loaded later on when program starts
        
        super().__init__(self.address,
                         on_open=self.handleOpen,
                         on_message=self.handleMessage,
                         on_error=self.handleError,
                         on_close=self.handleClose)
        
    def createSession(self) -> Client:
        session = Client()
        session.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": generate_user_agent()
        }
        return session
        
    def handleOpen(self, ws) -> None:
        global AUTH_PAYLOAD_SENT
        payload = {
            "op": 2,
            "d": {
                "intents": 1,
                "token": self.token,
                "properties": {
                    "$os": "linux",
                    "$browser": "firefox",
                    "$device": "pc"
                }
            }
        }
        self.send(json.dumps(payload))
        AUTH_PAYLOAD_SENT = True
        os.system(f"title [ vanity sniper ] [ total heartbeat sent: {TOTAL_HEARTBEAT_SENT} ] [ auth payload sent: {AUTH_PAYLOAD_SENT} ]")
        
    def handleMessage(self, ws, message) -> None:
        data = json.loads(message)
        
        if data.get('op') == 10:
            heartbeatInterval = int(data['d']['heartbeat_interval']) / 1000
            self.heartbeatInterval = heartbeatInterval
            Thread(target=self.heartbeatCycle).start()
            print('WEBSOCKET - Heartbeat cycle started - Interval in seconds:', self.heartbeatInterval)
        elif data.get('t') == 'GUILD_UPDATE':
            self.claimVanity(data)
            
    def handleError(self, ws, error) -> None:
        print('WEBSOCKET ERROR - Error:', error)
        print('WEBSOCKET - Reconnecting..')
        self.close()
        self.run_forever()

    def handleClose(self, ws, statusCode, closeMsg) -> None:
        print(f'WEBSOCKET CLOSED - Status code: {statusCode} - Reason: {closeMsg}')
        print('WEBSOCKET - Reconnecting..')
        self.close()
        self.run_forever()
            
    def heartbeatCycle(self) -> None:
        global TOTAL_HEARTBEAT_SENT
        heartbeat = {
            'op': 1,
            'd': 251
        }
        while True:
            self.send(json.dumps(heartbeat))
            TOTAL_HEARTBEAT_SENT += 1
            os.system(f"title [ vanity sniper ] [ total heartbeat sent: {TOTAL_HEARTBEAT_SENT} ] [ auth payload sent: {AUTH_PAYLOAD_SENT} ]")
            time.sleep(self.heartbeatInterval)
            
    def claimVanity(self, data) -> None:
        start = time.time()
        if data['d']['guild_id'] == self.targetGuild:
            if data['d']['vanity_url_code'] != self.targetVanity:
                response = self.session.patch(f"https://discord.com/api/v10/guilds/{self.claimGuild}", json={"code": self.targetVanity})
                if response.status_code == 200:
                    latency = time.time() - start
                    print(f"SNIPER - Target vanity is succesfully claimed in {round(latency * 1000)}ms")
                else:
                    print("SNIPER - I failed while claiming the vanity:", response.json())
            
if __name__ == '__main__':
    os.system(f"title [ vanity sniper ] [ total heartbeat sent: {TOTAL_HEARTBEAT_SENT} ] [ auth payload sent: {AUTH_PAYLOAD_SENT} ]")
    sniper = Sniper()
    sniper.run_forever()
