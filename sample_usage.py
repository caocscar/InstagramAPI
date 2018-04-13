# -*- coding: utf-8 -*-
import instagram_api_functions as IG
import pandas as pd

pd.options.display.max_rows = 16

#%% Get ids of users
usernames = ['umichhockey']
profiles = IG.get_user_id(usernames)

#%% Specify user
for username in profiles.keys():
    print(username)
    uid = profiles[username]
    
    #%% Get user posts
    posts = IG.get_user_posts(uid, geocode=False)
    posts['text'] = posts['text'].apply(lambda x: x.replace('\n',' ').replace('\r',' '))
    posts.to_csv('{}_posts.txt'.format(username), index=False, sep='|', encoding='utf-8')
    
    #%% Download media for specific posts
    if posts.shape[0] > 0: #check if there are any posts
        media_ids = posts['media_id'].tolist()
        IG.get_user_media(uid)

        # Get comments for specific posts
        with open('{}_comments.txt'.format(username), 'w', encoding='utf-8') as fout:
            for i, media_id in enumerate(media_ids, start=1):
                header_flag = True if i == 1 else False
                print('{}, Media {}'.format(i, media_id))
                comments = IG.get_post_comments(media_id)
                comments.insert(0,'media_id',media_id)       
                comments.to_csv(fout, index=False, sep='|', header=header_flag)



