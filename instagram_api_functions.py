# -*- coding: utf-8 -*-
"""
This script contains functions to do the following:
    Get user id for username based on exact match.
    Get timestamp of first post for user.
    Gets metadata about a user.
    Iterates through a user's timeline and extracts post and metadata.
    Downloads Instagram Media given a url.
    Iterates through a user's timeline and downloads the associated media.
    Gets media id for a given url.
    Get comments for a particular post (media).    

You will need to install the Instagram API module and/or the GoogleMaps module
(for geocoding) located here on Github:
https://github.com/LevPasha/Instagram-API-python
https://github.com/googlemaps/google-maps-services-python

IMPORTANT:
You also need to include your login information after the import statements
"""

from InstagramAPI import InstagramAPI
import os
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import googlemaps

username = 'username'
pwd = 'password'
API = InstagramAPI(username,pwd)
API.login()

#%%
def get_user_id(usernames):
    """
    Get user id for username based on exact match.
        
    Parameters
    ----------
    usernames: list
        List of usernames
  
    Returns
    -------
    dictionary
        key, value = user, user id
    """
    
    profiles = {}
    if not isinstance(usernames, list):
        usernames = list(usernames)
    for username in usernames:
        API.fbUserSearch(username)
        response = API.LastJson
        for account in response['users']:
            if account['user']['username'] == username:
                profiles[username]= account['user']['pk']
                break
    return profiles

    
def get_first_post_timestamp(uid):
    """
    Get timestamp of first post for user.

    Parameters
    ----------
    uid: str
        User id
  
    Returns
    -------
    tuple
        two-tuple of timestamp and max_id
    """
    
    timestamp = None
    ts = pd.read_csv('max_id_timestamps.txt')
    for row in ts.itertuples(index=False):
        max_id = row[1]
        while True:
            API.getUserFeed(uid, maxid=max_id)
            response = API.LastJson
            if response['num_results'] == 0:
                break
            item = response['items'][-1]
            caption = item['caption']
            seconds = caption['created_at'] if caption else item['taken_at']
            tiempo = datetime.fromtimestamp(seconds)
            timestamp = tiempo.strftime('%Y-%m-%d %H:%M:%S')
            max_id = item['id']
            print(timestamp, max_id)
            if not response['more_available']:
                break
        if timestamp:
            break
    return (timestamp, max_id)


def get_user_metadata(profiles):
    """
    Gets metadata about a user.
    
    Parameters
    ----------
    profiles: dict
        Dictionary of users
  
    Returns
    -------
    DataFrame
        Columns: ['username','posts','followers','following','first_post',
                  'max_id']        
    """
    
    metadata = []
    for username in profiles.keys():
        print('Processing {}'.format(username) )
        uid = profiles[username]
        API.getUsernameInfo(uid)
        response = API.LastJson
        posts = response['user']['media_count'] 
        followers = response['user']['follower_count']
        following = response['user']['following_count']
        timestamp, max_id = get_first_post_timestamp(uid)
        metadata.append((username,posts,followers,following,timestamp,max_id))
    columns = columns=['username','posts','followers','following','first_post','max_id']
    return pd.DataFrame(metadata, columns=columns)
    

def get_user_posts(uid, *, max_id = '', count=15000, geocode=False):
    """
    Iterates through a user's timeline and extracts post and metadata.
    
    Parameters
    ----------
    uid: int
        User id
    max_id: str
        Return post earlier than this max_id
    count: int
        Count of posts to return
    geocode: boolean              
        Whether to geocode the lon/lat coordinates if exists using 
        Google Maps API. True for geocoding. False for no geocoding.
  
    Returns
    -------
    DataFrame
        Columns: ['media_id','shortcode','timestamp','weekday','lon',
                  'lat','address','like_count','comment_count','media_type',
                  'duration','views','photos','text']
    """
    
    if geocode:
        apikey = os.getenv('GOOGLE_MAP_API_KEY') # Insert own key HERE
        gmaps = googlemaps.Client(apikey)    
    data = []
    counter = 0
    if not isinstance(max_id, str):
        max_id = str(max_id)
    while counter < count:
        print('Post {} {}'.format(counter, max_id))
        API.getUserFeed(uid, maxid=max_id)
        response = API.LastJson
        for i, item in enumerate(response['items'], start=counter+1):
            media_id = item['pk']
            shortcode = item['code']
            if item['caption']:
                seconds = item['caption']['created_at']
                txt = item['caption']['text']
            else:
                seconds = item['taken_at']
                txt = ''
            tiempo = datetime.fromtimestamp(seconds)
            timestamp = tiempo.strftime('%Y-%m-%d %H:%M:%S')
            weekday = tiempo.isoweekday()
            if 'lng' in item:
                lon, lat = item['lng'], item['lat']
                address = gmaps.reverse_geocode((lat, lon))[0]['formatted_address'] if geocode else None
            else:
                lon, lat, address = None, None, None
            likes = item['like_count']
            comments = item.get('comment_count',0)
            media = item['media_type']
            duration = item.get('video_duration', None)
            views = item.get('view_count', None)
            photos = len(item['carousel_media']) if media == 8 else 1
            data.append((media_id, shortcode, timestamp, weekday, lon, lat, address, likes, comments, media, duration, views, photos, txt))
            if i >= count:
                break
        counter = i
        if response['more_available']:
            max_id = response['next_max_id']
        else:
            break
        
    columns = ['media_id','shortcode','timestamp','weekday','lon','lat','address','like_count','comment_count','media_type','duration','views','photos','text']        
    return pd.DataFrame(data, columns=columns)    

    
def download_media(url, filename, *, photo=True):
    """
    Downloads Instagram Media given a url.
    
    Parameters
    ----------
    url: str
        Url of media
    filename: str
        Filename of downloaded media
    photo: boolean
        Whether media is a photo. True if photo. False if video.        
        
    Returns
    -------
    file
        Downloaded media
    """
    
    R = requests.get(url)
    if R.status_code == 404:
        print('url not found for media {}'.format(filename))  
        return
    else:
        R.raise_for_status()
    with open(filename, 'wb') as fout:
        if photo:           
            fout.write(R.content)
        else: # video
            for chunk in R.iter_content(chunk_size=255): 
                if chunk: # filter out keep-alive new chunks
                    fout.write(chunk)
    print('{} downloaded'.format(filename))


def get_user_media(uid, *, max_id = '', count=15000, filter=False, media_ids=[]):
    """
    Iterates through a user's timeline and downloads the associated media.
    
    Parameters
    ----------
    uid: int
        User id
    max_id: str
        Return media earlier than this max_id
    count: int
        Count of media to return
    filter: boolean
        Whether to filter for particular posts
    media_ids: list
        List of post ids to filter for (filter argument needs to be True)                
    """    
    
    counter = 0
    media_count = 0
    if not isinstance(max_id, str):
        max_id = str(max_id)
    if filter and not isinstance(media_ids, list):
        media_ids = list(media_ids)
    while counter < count:
        print('Post {} {}'.format(counter, max_id))
        API.getUserFeed(uid, maxid=max_id)
        response = API.LastJson
        for i, item in enumerate(response['items'], start=counter+1):
            media_id = item['pk']
            if filter: # filtering media
                assert type(media_id) == type(media_ids[0])
                if media_id not in media_ids:
                    continue
                else:
                    media_count += 1
            media = item['media_type']
            filename = '{4}_{2}_{3:0>2}.jpg'.format(username,i,media,1,media_id)
            if media == 1: # not a slide show (carousel)
                url = item['image_versions2']['candidates'][0]['url']
                download_media(url, filename)
            elif media == 8: # carousel
                for k, photo in enumerate(item['carousel_media'], start=1):
                    filename = '{4}_{2}_{3:0>2}.jpg'.format(username,i,media,k,media_id)
                    url = photo['image_versions2']['candidates'][0]['url']
                    download_media(url, filename)
            elif media == 2: # video
                if 'video_dash_manifest' in item:
                    html = item.get('video_dash_manifest')
                    soup = BeautifulSoup(html, 'html.parser')
                    videolinks = soup.find_all('baseurl')
                    if videolinks:
                        url = videolinks[0].text 
                    else:
                        print('Could NOT find video link for {}'.format(media_id))
                        assert 1>2
                elif 'video_versions' in item:
                    url = item['video_versions'][0]['url']
                else:
                    print('Unknown key to access video url for {}'.format(media_id))
                    assert 1>2                
                extension = os.path.splitext(url)[-1]
                filename = '{0}{1}'.format(media_id,extension)
                download_media(url, filename, photo=False)
            else:
                print('Unknown Media Type for {}'.format(media_id))
                assert 1>2
            if i >= count:                
                break
            if filter: # checking if all media has been obtained
                if media_count == len(media_ids):
                    return
        counter = i
        if response['more_available']:
            max_id = response['next_max_id']
        else:
            return    

    
def get_media_id(url):
    """
    Gets media id for a given url.
    
    Parameters
    ----------
    url: str
        Url of media
    
    Returns
    -------
    str
        Media id
    """
    
    callback_url = 'http://www.google.com'
    get_mediaid_url = r'http://api.instagram.com/oembed?callback={}&url={}'.format(callback_url,url)
    R = requests.get(get_mediaid_url)
    R.raise_for_status()
    response = R.json()
    return response['media_id']

    
def get_post_comments(media_id, *, max_id='', count=100000):
    """
    Get comments for a particular post (media).
    
    Parameters
    ----------
    media_id: str
        Media id
    max_id: str
        Return comment earlier than this max_id
    count: int
        Count of comments to return
                
    Returns
    -------
    DataFrame
        Columns: ['timestamp','name','userid','text']
        Sorted by timestamp
    """
    
    columns = ['timestamp','name','userid','text']
    comments = []
    counter = 0
    if not isinstance(media_id, str):
        media_id = str(media_id)
    if not isinstance(max_id, str):
        max_id = str(max_id)
    while counter < count:
        print('Comment {}'.format(counter) )
        API.getMediaComments(media_id, max_id=max_id)
        response = API.LastJson
        if response.get('comment_count',0) == 0:
            return pd.DataFrame(columns=columns)
        for i, comment in enumerate(response['comments'], start=counter+1):
            seconds = comment['created_at']
            tiempo = datetime.fromtimestamp(seconds)
            timestamp = tiempo.strftime('%Y-%m-%d %H:%M:%S')
            user = comment['user']['full_name']
            userid = comment['user_id']
            txt = comment['text']
            comments.append((timestamp, user, userid, txt))
            if i >= count:
                break
        counter = i
        if response['has_more_comments']:
            max_id = response['next_max_id']
        else:
            break    
    df = pd.DataFrame(comments, columns=columns)
    df.sort_values('timestamp', inplace=True)  
    df['text'] = df['text'].apply(lambda x: x.replace('\n',' ').replace('\r',' '))
    return df
    
    
    
    