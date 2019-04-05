import discord
import os
from datetime import datetime
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import threading

TOKEN = 'discord bot token'
channelID = 'discord channel id'
playlistID = 'youtube playlist id'
provider = "https://www.youtube.com/"
embedurl = "https://www.youtube.com/embed/"
harold = discord.Client()
youtube = False
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
jsonsecretfile = "client_secret_file.json"

@harold.event
async def on_ready():
    update_yt_list()
    await check_old(channelID)

@harold.event
async def on_resumed():
    update_yt_list()
    await check_old(channelID)
    
@harold.event
async def on_message(message):
    update_yt_list()
    for id in parse_message(message):
        yt_add(id)

@harold.event
async def on_message_edit(before, after):
    update_yt_list()
    for id in parse_message(before):
        yt_del(id)
    for id in parse_message(after):
        yt_add(id)

@harold.event
async def on_message_delete(message):
    update_yt_list()
    for id in parse_message(message):
        yt_del(id)

def parse_message(message):
    ids = []
    if message.channel.is_private == False and message.channel.id == channelID:
        if message.author == harold.user:
            return
        ids = []
        for embed in message.embeds:
            if embed.provider.url == provider:
                ids.append(parse_yt_id(embed.video.url))
    return ids

async def check_old(cid):
    threads = []
    chan = discord.Channel
    chan.id = channelID
    async for message in harold.logs_from(chan, limit=50, before=datetime.now()):
        print(message.content)
        for id in parse_message(message):
            print(id)
            t = threading.Thread(target=yt_add, args=(id,))
            t.start()
            threads.append(t)
    for t in threads:
        t.join()

def parse_yt_id(message):
    return message.replace(embedurl, "")
    
def yt_init():
    global youtube
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = jsonsecretfile
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
    
def yt_add(id):
    if not id in yt_list:
        request = youtube.playlistItems().insert(
        part="snippet",
        body={
          "snippet": {
            "playlistId": playlistID,
            "position": 0,
            "resourceId": {
              "kind": "youtube#video",
              "videoId": id
            }
          }
        }
    )
    print(request.execute())

def yt_del(id):
    itemID = False
    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            maxResults=50,
            pageToken=npt,
            playlistId=playlistID
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
        request = youtube.playlistItems().delete(
            id=itemID
        )
        print(request.execute())
        return True
    else:
        return False

def update_yt_list():
    ids = []
    npt = ""
    global yt_list
    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            maxResults=50,
            pageToken=npt,
            playlistId=playlistID
        )
        response = request.execute()
        for r in response['items']:
            if r['snippet']['resourceId']['kind'] == "youtube#video":
                ids.append(r['snippet']['resourceId']['videoId'])
        if 'nextPageToken' in response:
            npt = response['nextPageToken']
        else:
            break
    yt_list = ids

yt_init()
harold.run(TOKEN)