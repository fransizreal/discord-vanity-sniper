import os
import json
import time

from httpx import Client
from websocket import WebSocketApp
from user_agent import generate_user_agent
from threading import Thread

from colorama import Fore, Style, init
from datetime import datetime

TOTAL_HEARTBEAT_SENT = 0

class Log:
    def __init__(self, message, topic):
        self.message = message
        self.topic = topic
        
    def getTimestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")
        
    def sendLog(self) -> str:
        return f'{Style.BRIGHT}{Fore.BLACK}{self.getTimestamp()}{Fore.RESET} - {Fore.MAGENTA}{self.topic.upper()}{Fore.RESET} - {self.message}'

class Sniper(WebSocketApp):
    def __init__(self):
        config = self.loadConfig()
        
        self.token = config["token"]
        self.targetGuild = config["targetGuild"]
        self.claimGuild = config["claimGuild"]
        self.targetVanity = config["targetVanity"]
        
        self.websocketVersion = 7 # recommended, but you can change it as your wish
        self.session = self.createSession()
        
        self.address = f"wss://gateway.discord.gg/?v={self.websocketVersion}&encoding=json"
        self.heartbeatInterval = None # do not touch it just because its a none type object, it will be loaded later on when program starts
        
        super().__init__(self.address,
                         on_open=self.handleOpen,
                         on_message=self.handleMessage,
                         on_error=self.handleError,
                         on_close=self.handleClose)
        
    def handleOpen(self, ws) -> None:
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
        print(Log('Authorization payload sent', 'token').sendLog())
        
    def handleMessage(self, ws, message) -> None:
        data = json.loads(message)
        
        if data.get('op') == 10:
            heartbeatInterval = int(data['d']['heartbeat_interval']) / 1000
            self.heartbeatInterval = heartbeatInterval
            Thread(target=self.heartbeatCycle).start()
            print(Log(f'Heartbeat interval in seconds: {self.heartbeatInterval}', 'keep-alive').sendLog())
        elif data.get('t') == 'GUILD_UPDATE':
            self.claimVanity(data)
            
    def handleError(self, ws, error) -> None:
        print(Log(f'Error: {error}', 'websocket').sendLog())
        self.reconnectToWs()

    def handleClose(self, ws, statusCode, closeMsg) -> None:
        print(Log(f'Status code: {statusCode}, reason: {closeMsg}', 'websocket').sendLog())
        self.reconnectToWs()
        
    def createSession(self) -> Client:
        session = Client()
        session.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": generate_user_agent()
        }
        print(Log('HTTP session is succesfully created', 'session').sendLog())
        return session
            
    def heartbeatCycle(self) -> None:
        global TOTAL_HEARTBEAT_SENT
        heartbeat = {
            'op': 1,
            'd': 251
        }
        while True:
            self.send(json.dumps(heartbeat))
            TOTAL_HEARTBEAT_SENT += 1
            os.system(f"title [ vanity sniper ] [ total heartbeat sent: {TOTAL_HEARTBEAT_SENT} ]")
            time.sleep(self.heartbeatInterval)
            
    def claimVanity(self, data) -> None:
        start = time.time()
        if data['d']['guild_id'] == self.targetGuild:
            if data['d']['vanity_url_code'] != self.targetVanity:
                response = self.session.patch(f"https://discord.com/api/v10/guilds/{self.claimGuild}", json={"code": self.targetVanity})
                if response.status_code == 200:
                    latency = time.time() - start
                    print(Log(f"Target vanity is succesfully claimed in {round(latency * 1000)}ms", 'sniper').sendLog())
                else:
                    print(Log('I failed to claim the vanity', 'sniper').sendLog())
                    
    def loadConfig(self) -> None:
        with open("config.json", "r", encoding="utf-8") as file:
            return json.load(file)
        
    def reconnectToWs(self) -> None:
        self.close()
        print(Log("I've closed client socket because an error occured on websocket, now reconnecting", 'info').sendLog())
        print()
        self.run_forever()
            
if __name__ == '__main__':
    os.system("mode 100, 25")
    os.system(f"title [ vanity sniper ] [ total heartbeat sent: {TOTAL_HEARTBEAT_SENT} ]")
    sniper = Sniper()
    sniper.run_forever()
