#!/usr/bin/env python
import math
from os import name
from pathlib import Path
from subprocess import Popen

from prawcore import ResponseException
from reddit.subreddit import get_subreddit_threads
from utils import settings
from utils.cleanup import cleanup
from utils.console import print_markdown, print_step
from utils.id import id
from video_creation.background import (
    download_background,
    chop_background_video,
    get_background_config,
)
from video_creation.final_video import make_final_video
from video_creation.screenshot_downloader import get_screenshots_of_reddit_posts
from video_creation.voices import save_text_to_mp3
from utils.ffmpeg_install import ffmpeg_install

__VERSION__ = "3.1"

print(
    """MAKER READY TO START"""
)


def main(POST_ID=None) -> None:
    global redditid, reddit_object
    reddit_object = get_subreddit_threads(POST_ID)
    redditid = id(reddit_object)
    length, number_of_comments = save_text_to_mp3(reddit_object)
    length = math.ceil(length)
    get_screenshots_of_reddit_posts(reddit_object, number_of_comments)
    bg_config = get_background_config()
    download_background(bg_config)
    chop_background_video(bg_config, length, reddit_object)
    make_final_video(number_of_comments, length, reddit_object, bg_config)

def shutdown():
    try:
        redditid
    except NameError:
        print("Exiting...")
        exit()
    else:
        print_markdown("## Clearing temp files")
        cleanup(redditid)
        print("Exiting...")
        exit()


if __name__ == "__main__":

    directory = Path().absolute()
    config = settings.check_toml(
        f"{directory}/utils/.config.template.toml", "config.toml"
    )
    config is False and exit()
    
    try:
        while(True):
            main()

    except KeyboardInterrupt:
        shutdown()
    except ResponseException:
        # error for invalid credentials
        print_markdown("## Invalid credentials")
        print_markdown("Please check your credentials in the config.toml file")

        shutdown()
        main()
        
    except Exception as err:
        config["settings"]["tts"]["tiktok_sessionid"] = "REDACTED"
        print_step(
            f"Sorry, something went wrong with this version! Try again, and feel free to report this issue at GitHub or the Discord community.\n"
            f"Version: {__VERSION__} \n"
            f"Error: {err} \n"
            f'Config: {config["settings"]}'
        )
        main()
    
        
