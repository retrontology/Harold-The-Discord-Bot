import discord
import os
from datetime import datetime
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
import re
import sys
from urllib import parse
from harold_config import harold_config
import pickle


class Harold(discord.Client):

    def __init__(self, config, *args, **kwargs):
        self.config = config
        self.youtube = self.yt_init()
        super(Harold, self).__init__(*args, **kwargs)

    async def on_ready(self):
        self.update_yt_list()
        await self.check_old(self.config['discord']['channelID'])

    async def on_resumed(self):
        self.update_yt_list()
        await self.check_old(self.config['discord']['channelID'])

    async def on_message(self, message):
        self.update_yt_list()
        for id in self.parse_message_content(message):
            self.yt_add(id)

    # async def on_message_edit(before, after):
    #     update_yt_list()
    #     for id in parse_message_content(before):
    #         yt_del(id)
    #     for id in parse_message_content(after):
    #         yt_add(id)

    async def on_message_delete(self, message):
        self.update_yt_list()
        for id in self.parse_message_content(message):
            self.yt_del(id)
    
    def parse_message_content(self, message):
        ids = []
        if message.channel.id == self.config['discord']['channelID']:
            print("Parsing following message content for youtube links: \r\n" + message.content)
            if message.author == self.user:
                return
            for r in re.findall(r'(https?://\S+)', message.content):
                url = parse.urlparse(r)
                if url.netloc in ['youtu.be','m.youtube.com','www.youtube.com','youtube.com']:
                    if url.path == "/watch":
                        for q in parse.parse_qsl(url.query):
                            if q[0] == 'v':
                                print("Found: " + q[1])
                                ids.append(q[1])
                                break
                    else:
                        ids.append(url.path.replace("/",""))
                        print("Found: " + url.path.replace("/",""))
        return ids

    async def check_old(self, channelID):
        async for message in self.get_channel(channelID).history():
            for id in self.parse_message_content(message):
                print(id)
                self.yt_add(id)
    
    def yt_init(self):
        api_name = 'youtube'
        api_version = 'v3'
        scopes = ['https://www.googleapis.com/auth/youtube.force-ssl']
        pickle_dir = os.path.join(os.path.dirname(__file__), 'pickles')
        if not os.path.exists(pickle_dir):
            os.mkdir(pickle_dir)
        pickle_file = os.path.join(pickle_dir, f'token_Harold.pickle')
        creds = None
        if os.path.exists(pickle_file):
            with open(pickle_file, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.config['youtube']['json'], scopes)
                creds = flow.run_console()
            with open(pickle_file, 'wb') as token:
                pickle.dump(creds, token)
        return build(api_name, api_version, credentials=creds)
    
    def yt_add(self, id):
        if not id in self.yt_list:
            request = self.youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": self.config['youtube']['playlistID'],
                    "position": 0,
                    "resourceId": {
                    "kind": "youtube#video",
                    "videoId": id
                    }
                }
            }
        )
        try:
            r = request.execute()
            print(r)
        except:
            e = sys.exc_info()[0]
            print(e)

    def yt_del(self, id):
        itemID = False
        npt = ""
        while True:
            request = self.youtube.playlistItems().list(
                part="snippet",
                maxResults=50,
                pageToken=npt,
                playlistId=self.config['youtube']['playlistID']
            )
            response = request.execute()
            for r in response['items']:
                if r['snippet']['resourceId']['kind'] == "youtube#video" and r['snippet']['resourceId']['videoId'] == id:
                    itemID = r['id']
                    break
            if 'nextPageToken' in response and not itemID:
                npt = response['nextPageToken']
            else:
                break
        if itemID:
            request = self.youtube.playlistItems().delete(id=itemID)
            try:
                r = request.execute()
                print(r)
            except:
                e = sys.exc_info()[0]
                print(e)
            return True
        else:
            return False

    def update_yt_list(self):
        ids = []
        npt = ""
        while True:
            request = self.youtube.playlistItems().list(
                part="snippet",
                maxResults=50,
                pageToken=npt,
                playlistId=self.config['youtube']['playlistID']
            )
            response = request.execute()
            for r in response['items']:
                if r['snippet']['resourceId']['kind'] == "youtube#video":
                    ids.append(r['snippet']['resourceId']['videoId'])
            if 'nextPageToken' in response:
                npt = response['nextPageToken']
            else:
                break
        self.yt_list = ids


def main():
    config = harold_config('config.yaml')
    harold = Harold(config)
    harold.run(config['discord']['token'])


if __name__ == '__main__':
    main()