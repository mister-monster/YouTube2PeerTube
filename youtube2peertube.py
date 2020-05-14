#!/usr/bin/python3

import sys
import getopt
import pafy
import feedparser as fp
from urllib.request import urlretrieve
import requests
import json
from time import sleep
from os import mkdir, path
from shutil import rmtree
import mimetypes
from requests_toolbelt.multipart.encoder import MultipartEncoder
import utils

def get_video_data(channel_id):
    yt_rss_url = "https://www.youtube.com/feeds/videos.xml?channel_id=" + channel_id
    feed = fp.parse(yt_rss_url)
    channel_lang = feed["feed"]["title_detail"]["language"]
    print(feed["feed"])
    entries = feed["entries"]
    channels_timestamps = "channels_timestamps.csv"
    # clear any existing queue before start
    queue = []
    # read contents of channels_timestamps.csv, create list object of contents
    ct = open(channels_timestamps, "r")
    ctr = ct.read().split("\n")
    ct.close()
    ctr_line = []
    channel_found = False
    # check if channel ID is found in channels_timestamps.csv
    for line in ctr:
        line_list = line.split(',')
        if channel_id == line_list[0]:
            channel_found = True
            ctr_line = line
            break
    if not channel_found:
        print("new channel added to config: " + channel_id)
    print(channel_id)
    # iterate through video entries for channel, parse data into objects for use
    for pos, i in enumerate(reversed(entries)):
        published = i["published"]
        updated = i["updated"]
        if not channel_found:
            # add the video to the queue
            queue.append(i)
            ctr_line = str(channel_id + "," + published + "," + updated + '\n')
            # add the new line to ctr for adding to channels_timestamps later
            ctr.append(ctr_line)
            channel_found = True
        # if the channel exists in channels_timestamps, update "published" time in the channel line
        else:
            published_int = utils.convert_timestamp(published)
            ctr_line_list = ctr_line.split(",")
            line_published_int = utils.convert_timestamp(ctr_line_list[1])
            if published_int > line_published_int:
                # update the timestamp in the line for the channel in channels_timestamps,
                ctr.remove(ctr_line)
                ctr_line = str(channel_id + "," + published + "," + updated + '\n')
                ctr.append(ctr_line)
                # and add current videos to queue.
                queue.append(i)
        print(published)
    # write the new channels and timestamps line to channels_timestamps.csv
    ct = open(channels_timestamps, "w")
    for line in ctr:
        if line != '':
            ct.write(line + "\n")
    ct.close()
    return queue, channel_lang

def download_yt_video(queue_item, dl_dir, channel_conf):
    url = queue_item["link"]
    dl_dir = dl_dir + channel_conf["name"]
    try:
        video = pafy.new(url)
        streams = video.streams
        #for s in streams:
            #print(s.resolution, s.extension, s.get_filesize, s.url)
        best = video.getbest(preftype=channel_conf["preferred_extension"])
        filepath = dl_dir + "/"+ queue_item["yt_videoid"] + "." + channel_conf["preferred_extension"]
        #TODO: implement resolution logic from config, currently downloading best resolution
        best.download(filepath=filepath, quiet=False)

    except:
        pass
        # TODO: check YT alternate URL for video availability
        # TODO: print and log exceptions

def save_metadata(queue_item, dl_dir, channel_conf):
    dl_dir = dl_dir + channel_conf["name"]
    link = queue_item["link"]
    title = queue_item["title"]
    description = queue_item["summary"]
    author = queue_item["author"]
    published = queue_item["published"]
    metadata_file = dl_dir + "/" + queue_item["yt_videoid"] + ".txt"
    metadata = open(metadata_file, "w+")
    # save relevant metadata as semicolon separated easy to read values to text file
    metadata.write('title: "' + title + '";\n\nlink: "' + link + '";\n\nauthor: "' + author + '";\n\npublished: "' +
                   published + '";\n\ndescription: "' + description + '"\n\n;')
    # save raw metadata JSON string
    metadata.write(str(queue_item))
    metadata.close()

def save_thumbnail(queue_item, dl_dir, channel_conf):
    dl_dir = dl_dir + channel_conf["name"]
    thumb = str(queue_item["media_thumbnail"][0]["url"])
    extension = thumb.split(".")[-1]
    thumb_file = dl_dir + "/" + queue_item["yt_videoid"] + "." + extension
    # download the thumbnail
    urlretrieve(thumb, thumb_file)
    return extension

def get_pt_auth(channel_conf):
    # get variables from channel_conf
    pt_api = channel_conf["peertube_instance"] + "/api/v1"
    pt_uname = channel_conf["peertube_username"]
    pt_passwd = channel_conf["peertube_password"]
    # get client ID and secret from peertube instance
    id_secret = json.loads(str(requests.get(pt_api + "/oauth-clients/local").content).split("'")[1])
    client_id = id_secret["client_id"]
    client_secret = id_secret["client_secret"]
    # construct JSON for post request to get access token
    auth_json = {'client_id': client_id,
                 'client_secret': client_secret,
                 'grant_type': 'password',
                 'response_type': 'code',
                 'username': pt_uname,
                 'password': pt_passwd
                 }
    # get access token
    auth_result = json.loads(str(requests.post(pt_api + "/users/token", data=auth_json).content).split("'")[1])
    access_token = auth_result["access_token"]
    return access_token

def get_pt_channel_id(channel_conf):
    pt_api = channel_conf["peertube_instance"] + "/api/v1"
    post_url = pt_api + "/video-channels/" + channel_conf["peertube_channel"] + "/"
    returned_json = json.loads(requests.get(post_url).content)
    channel_id = returned_json["id"]
    return channel_id

def get_file(file_path):
    mimetypes.init()
    return (path.basename(file_path), open(path.abspath(file_path), 'rb'),
            mimetypes.types_map[path.splitext(file_path)[1]])


def handle_peertube_result(request_result):
    if request_result.status_code < 300:
        return True
    else:
        print(request_result)
        return False
    
def upload_to_pt(dl_dir, channel_conf, queue_item, access_token, thumb_extension):
    # Adapted from Prismedia https://git.lecygnenoir.info/LecygneNoir/prismedia
    pt_api = channel_conf["peertube_instance"] + "/api/v1"
    video_file = dl_dir + channel_conf["name"] + "/" + queue_item["yt_videoid"] + "." + \
                 channel_conf["preferred_extension"]
    thumb_file = dl_dir + channel_conf["name"] + "/" + queue_item["yt_videoid"] + "." + thumb_extension
    description = channel_conf["description_prefix"] + "\n\n" + queue_item["summary"] + "\n\n" + channel_conf["description_suffix"]
    channel_id = str(get_pt_channel_id(channel_conf))
    # We need to transform fields into tuple to deal with tags as
    # MultipartEncoder does not support list refer
    # https://github.com/requests/toolbelt/issues/190 and
    # https://github.com/requests/toolbelt/issues/205
    try:
        fields = [
            ("name", queue_item["title"]),
            ("licence", "1"),
            ("description", description),
            ("nsfw", channel_conf["nsfw"]),
            ("channelId", channel_id),
            ("originallyPublishedAt", queue_item["published"]),
            ("category", channel_conf["pt_channel_category"]),
            ("language", channel_conf["default_lang"]),
            ("privacy", str(channel_conf["pt_privacy"])),
            ("commentsEnabled", channel_conf["comments_enabled"]),
            ("videofile", get_file(video_file)),
            ("thumbnailfile", get_file(thumb_file)),
            ("previewfile", get_file(thumb_file)),
            ("waitTranscoding", 'false')
        ]
    except:
        return

    if channel_conf["pt_tags"] != "":
        fields.append(("tags", "[" + channel_conf["pt_tags"] + "]"))
    else:
        print("you have no tags in your configuration file for this channel")
    multipart_data = MultipartEncoder(fields)
    headers = {
        'Content-Type': multipart_data.content_type,
        'Authorization': "Bearer " + access_token
    }
    
    return handle_peertube_result(requests.post(pt_api + "/videos/upload", data=multipart_data, headers=headers))

def pt_http_import(dl_dir, channel_conf, queue_item, access_token, thumb_extension, yt_lang):
    # Adapted from Prismedia https://git.lecygnenoir.info/LecygneNoir/prismedia
    pt_api = channel_conf["peertube_instance"] + "/api/v1"
    yt_video_url = queue_item["link"]
    # TODO: use the alternate link if video not found error occurs
    alternate_link = queue_item["links"][0]["href"]
    thumb_file = dl_dir + channel_conf["name"] + "/" + queue_item["yt_videoid"] + "." + thumb_extension
    description = channel_conf["description_prefix"] + "\n\n" + queue_item["summary"] + "\n\n" + channel_conf["description_suffix"]
    channel_id = str(get_pt_channel_id(channel_conf))
    language = utils.set_pt_lang(yt_lang, channel_conf["default_lang"])
    category = utils.set_pt_category(channel_conf["pt_channel_category"])
    # We need to transform fields into tuple to deal with tags as
    # MultipartEncoder does not support list refer
    # https://github.com/requests/toolbelt/issues/190 and
    # https://github.com/requests/toolbelt/issues/205
    fields = [
        ("name", queue_item["title"]),
        ("licence", "1"),
        ("description", description),
        ("nsfw", channel_conf["nsfw"]),
        ("channelId", channel_id),
        ("originallyPublishedAt", queue_item["published"]),
        ("category", category),
        ("language", language),
        ("privacy", str(channel_conf["pt_privacy"])),
        ("commentsEnabled", channel_conf["comments_enabled"]),
        ("targetUrl", yt_video_url),
        ("thumbnailfile", get_file(thumb_file)),
        ("previewfile", get_file(thumb_file)),
        ("waitTranscoding", 'false')
    ]
    if channel_conf["pt_tags"] != "":
        fields.append(("tags[]", channel_conf["pt_tags"]))
    else:
        print("you have no tags in your configuration file for this channel")
    multipart_data = MultipartEncoder(fields)
    headers = {
        'Content-Type': multipart_data.content_type,
        'Authorization': "Bearer " + access_token
    }
    
    return handle_peertube_result(requests.post(pt_api + "/videos/imports", data=multipart_data, headers=headers))
        

def log_upload_error(yt_url,channel_conf):
    error_file = open("video_errors.csv", "a")
    error_file.write(channel_conf['name']+","+yt_url+"\n")
    error_file.close()
    print("error !")

def run_steps(conf):
    # TODO: logging
    channel = conf["channel"]
    # run loop for every channel in the configuration file
    global_conf = conf["global"]
    if conf["global"]["delete_videos"] == "true":
        delete_videos = True
    else:
        delete_videos = False
    # The following enables the deletion of thumbnails, videos are not downloaded at all
    if conf["global"]["use_pt_http_import"] == "true":
        delete_videos = True
        use_pt_http_import = True
    else:
        use_pt_http_import = False
    dl_dir = global_conf["video_download_dir"]
    if not path.exists(dl_dir):
        mkdir(dl_dir)
    channel_counter = 0
    for c in channel:
        print("\n")
        channel_id = channel[c]["channel_id"]
        channel_conf = channel[str(channel_counter)]
        video_data = get_video_data(channel_id)
        queue = video_data[0]
        yt_lang = video_data[1]
        if len(queue) > 0:
            if not path.exists(dl_dir + "/" + channel_conf["name"]):
                mkdir(dl_dir + "/" + channel_conf["name"])
            # download videos, metadata and thumbnails from youtube
            for queue_item in queue:
                if not use_pt_http_import:
                    print("downloading " + queue_item["yt_videoid"] + " from YouTube...")
                    download_yt_video(queue_item, dl_dir, channel_conf)
                    print("done.")
                # TODO: download closest to config specified resolution instead of best resolution
                thumb_extension = save_thumbnail(queue_item, dl_dir, channel_conf)
                # only save metadata to text file if archiving videos
                if not delete_videos:
                    print("saving video metadata...")
                    save_metadata(queue_item, dl_dir, channel_conf)
                    print("done.")
            access_token = get_pt_auth(channel_conf)
            # upload videos, metadata and thumbnails to peertube
            for queue_item in queue:
                if not use_pt_http_import:
                    print("uploading " + queue_item["yt_videoid"] + " to Peertube...")
                    pt_result = upload_to_pt(dl_dir, channel_conf, queue_item, access_token, thumb_extension)
                
                else:
                    print("mirroring " + queue_item["link"] + " to Peertube using HTTP import...")
                    pt_result = pt_http_import(dl_dir, channel_conf, queue_item, access_token, thumb_extension, yt_lang)

                if pt_result:
                    print("done !")
                else:
                    log_upload_error(queue_item["link"],channel_conf)
            if delete_videos:
                print("deleting videos and/or thumbnails...")
                rmtree(dl_dir + "/" + channel_conf["name"], ignore_errors=True)
                print("done")
        channel_counter += 1

def run(run_once=True):
    #TODO: turn this into a daemon
    conf = utils.read_conf("config.toml")
    if run_once:
        run_steps(conf)
    else:
        while True:
            poll_frequency = int(conf["global"]["poll_frequency"]) * 60
            run_steps(conf)
            sleep(poll_frequency)


def main(argv):
  run_once=False
  try:
    opts, args = getopt.getopt(argv,"ho",["help","once"])
  except:
    print("youtube2peertube.py [-o|--once]")
    sys(exit(2))

  for opt, arg in opts:
    if opt == '-h':
      print("youtube2peertube.py [-o|--once]")
      sys.exit()
    elif opt in ("-o", "--once"):
      run_once = True

  run(run_once)


if __name__ == "__main__":
  main(sys.argv[1:])
