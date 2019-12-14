# YouTube2PeerTube

YouTube2PeerTube is a bot written in Python3 that mirrors YouTube channels to PeerTube channels as videos are released in a YouTube channel.

It checks YouTube channels periodically, when new videos are found, it mirrors them with metadata to PeerTube corresponding peertube channels.

This tool supports multiple channels, and supports mirroring each YouTube channel to a user defined PeerTube channel and instance that can be different for each YouTube channel being mirrored.

This tool does not use YouTube APIs. Instead, it subscribes to channels via RSS. This is a primary feature, this tool will always avoid the YouTube API, and no features will be implemented that require the YouTube API.

If you need to archive a YouTube channel with lots of existing videos, this tool is not for you. This tool starts mirroring channels from the time they are added to the config and will not mirror all historical videos that exist in a YouTube channel. A tool that provides this functionality is available https://github.com/Chocobozzz/PeerTube/blob/develop/support/doc/tools.md#peertube-import-videosjs

## Installation

To install, clone the repository to a directory on your machine. Then, navigate to that directory in a terminal and run:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This will create a virtual environment for the tool and install all dependencies required to run.

## Dependencies

This tool depends on:

- pafy https://github.com/mps-youtube/pafy for downloading of YouTube content.

- feedparser for parsing of RSS data

- TOML for the configuration file

- MultipartEncoder from requests_toolbelt

- urllib.request, requests, mimetypes, time, json and os from the Python standard library

It also contains heavily modified components from prismedia https://git.lecygnenoir.info/LecygneNoir/prismedia for uploading videos and metadata to PeerTube.

## Configuration

IMPORTANT: If you are updating this tool be sure to check the new example configuration against your configuration, as some parameters may be added or removed or otherwise changed.

An example configuration file is found at example_config.toml. Copy this to config.toml and replace the fields with your information, and add channels as necessary.

The configuration file is found at config.toml. It allows you to configure the poll frequency for all YouTube channels, download directory for videos and metadata, whether to keep the videos after upload (for archiving purposes) as well as per channel options such as YouTube channel info, corresponding PeerTube channel info and auth, and appendable tags and descriptions.

If you set <use_pt_http_import> to "true", the bot will not download videos at all. It will simply pass the YT video URL to PeerTube directly. Because of this, if you choose to use this option, you will not be able to locally transcode videos, nor will you be able to archive them.

Each channel is capable of mirroring to a different PeerTube account and instance, and is capable of appending tags and description information on a per channel basis.

All videos and metadata are stored in <video_download_dir> as defined in the config, in a subdirectory with the same name as the channel <name> in the config, one directory per channel. All videos and metadata are named after the YouTube video ID. For each video, there should be 3 files: a video file, a thumbnail (jpg) and a text file containing metadata.

If <delete_videos> is set to True, videos and metadata will be deleted from the download directory after upload.

## Running the bot

To run the bot, simply run youtube2peertube.py. The bot will run indefinitely until stopped.

The first time a channel is found in the config, the most recent videos returned by the youtube RSS endpoint are mirrored, and a new entry is added to channels_timestamps.csv with the timestamp of the last video. Subsequently each channel is checked for an entry in channels_timestamps.csv and only videos later than the last timestamp for the channel's entry are mirrored. The tool decides if it is the first time a channel is found based on whether it has an entry in channels_timestamps.csv. It is designed this way so that the tool can be stopped and restarted without attempting to upload duplicate videos when restarted.

After that, the tool polls all channels in config.toml periodically based on the parameter <poll_frequency> which is in minutes, and mirrors all new videos for each channel as they are found.

Any time the configuration is changed, the bot must be restarted.

## Future improvements

- Auth info for PeerTube channels is currently stored in plaintext in config.toml. This is insecure and needs to be changed.

- It would be better if the tool were to run as a cron job or daemon rather than an ongoing python process.

- implement logging

- Sometimes a YouTube video or its metadata might be updated for some reason or other, it would be nice if the tool were able to update the mirrored video on PeerTube when this happens, and potentially archive or remove the previous version of the video.

- Currently there is no way to abide by the upload cap for PeerTube instances, this can lead to errors. It is recommended for now that you run your own PeerTube instance with no cap, or select PeerTube instances with high enough caps to account for the upload frequency of the YouTube accounts you are mirroring, and lower the upload resolution if needed (resolution preference not implemented yet). I would like to implement queue functionality for videos when the cap is reached, but I am unsure when I will implement this.

- A TUI would be nice for adding channels and restarting the bot.

See open issues for more details.

Please open issues if you find any problems or if you have a feature request. Pull requests are always welcome, however feature requests and pull requests will not be implemented if they are out of the scope of the project or if they cause issues with other existing features.

## Thanks!

Thanks to the mps-youtube project https://github.com/mps-youtube for pafy, and thanks to LecygneNoir https://git.lecygnenoir.info/LecygneNoir for the prismedia project. Thank you Tom for TOML and as always, Guido and the Python team.

If you find this tool useful and would like to donate, the following donation options are available:

XMR: 4AeufJrhpQn7LGW5dZ9tH4FFAtfmRwEDvhYrH5GQDbNxQ9VyWKmdycb5naWcvRTqbm3fkyqrDi23x453stDKzu5YVgPfcbj

BTC legacy: 141HaN7bq781BaB2PRP8mkUndebZXjxiFU

BTC segwit compatible: bc1qx2fa50av3j9hrjnszsnpflmtxqnz08936mq4xx

BCH: qzr9gk7tv274x9u9sft243m729zrjnq0cvpzlelapt

LTC: ltc1qa8re5eh2dklzfhg2x03tswsr5wae68qfxjzacd

ETH: 0x18304c5ed37dacefc920b291f39b06545b5fc258

ETC: 0xee3947eec103346ed42302221d99027a59bfa061

Buy me a cup of coffee!
