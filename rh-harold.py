import discord
import os
from datetime import datetime
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import re
import sys
from urllib import parse

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
    for id in parse_message_content(message):
        yt_add(id)

#@harold.event
#async def on_message_edit(before, after):
    #update_yt_list()
    #for id in parse_message_content(before):
        #yt_del(id)
    #for id in parse_message_content(after):
        #yt_add(id)

@harold.event
async def on_message_delete(message):
    update_yt_list()
    for id in parse_message_content(message):
        yt_del(id)

def parse_message_embed(message):
    ids = []
    if message.channel.id == channelID:
        if message.author == harold.user:
            return
        ids = []
        for embed in message.embeds:
            if embed.provider.url == provider:
                ids.append(parse_yt_id(embed.video.url))
    return ids
    
def parse_message_content(message):
    ids = []
    if message.channel.id == channelID:
        print("Parsing following message content for youtube links: \r\n" + message.content)
        if message.author == harold.user:
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

async def check_old(cid):
    threads = []
    chan = discord.Channel
    chan.id = cid
    async for message in harold.logs_from(chan, limit=200, before=datetime.now()):
        print(message.content)
        for id in parse_message_content(message):
            print(id)
            yt_add(id)

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
    try:
        r = request.execute()
        print(r)
    except:
        e = sys.exc_info()[0]
        print(e)

def yt_del(id):
    itemID = False
    npt = ""
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
        try:
            r = request.execute()
            print(r)
        except:
            e = sys.exc_info()[0]
            print(e)
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