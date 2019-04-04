import discord
import os
import datetime
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
#from multiprocessing.dummy import Pool as ThreadPool 

TOKEN = 'discord bot token'
channelID = 'discord channel id'
playlistID = 'youtube playlist id'
provider = "https://www.youtube.com/"
embedurl = "https://www.youtube.com/embed/"
harold = discord.Client()
#pool = ThreadPool(12)
youtube = False
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
jsonsecretfile = "client_secret_file.json"

@harold.event
async def on_ready():
    check_old(channelID)

@harold.event
async def on_resumed():
    check_old(channelID)
    
@harold.event
async def on_message(message):
    for id in parse_message(message):
        yt_add(id)

@harold.event
async def on_message_edit(before, after):
    for id in parse_message(before):
        yt_del(id)
    for id in parse_message(after):
        yt_add(id)

@harold.event
async def on_message_delete(message):
    yt_del(parse_message(message))

def parse_message(message):
    ids = []
    if message.channel.is_private == False and message.channel.id == channelID:
        if message.author == harold.user:
            return
        ids = []
        for embed in message.embeds:
            if embed.provider.url == provider:
                ids.append(parse_yt_id(embed.video.url))
    if ids == []:
        ids = False
    return ids

def check_old(cid):
    for message in harold.logs_from(channelID, limit=5000, before datetime.now):
        for id in parse_message(message):
            yt_add(id)

def parse_yt_id(message):
    return message.replace(embedurl, "")
    
def yt_init():
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = jsonsecretfile
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
    
def yt_add(id):
    if not yt_check(id):
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
    response = request.execute()

def yt_del(id):
    if yt_check(id):
        

def yt_check(id):
    return (id in yt_list)

def yt_list():
    ids = []
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=1000,
        playlistId=playlistID
    )
    response = request.execute()
    for r in response:
        if r.snippet.resourceId.kind == "youtube#video":
            ids.append(r.snippet.resourceId.videoId)
    if ids == []:
        ids = False
    return ids

yt_init()
harold.run(TOKEN)