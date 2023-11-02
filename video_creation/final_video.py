import multiprocessing
import os
from mutagen.mp3 import MP3
import re
import shutil
from os.path import exists # Needs to be imported specifically
from typing import Final
from typing import Tuple, Any

import ffmpeg
import translators as ts
from PIL import Image
from rich.console import Console
from rich.progress import track

from utils import settings
from utils.cleanup import cleanup
from utils.console import print_step, print_substep
from utils.thumbnail import create_thumbnail
from utils.videos import save_data

console = Console()

import tempfile
import threading
import time


class ProgressFfmpeg(threading.Thread):
    def __init__(self, vid_duration_seconds, progress_update_callback):
        threading.Thread.__init__(self, name="ProgressFfmpeg")
        self.stop_event = threading.Event()
        self.output_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        self.vid_duration_seconds = vid_duration_seconds
        self.progress_update_callback = progress_update_callback

    def run(self):
        while not self.stop_event.is_set():
            latest_progress = self.get_latest_ms_progress()
            if latest_progress is not None:
                completed_percent = latest_progress / self.vid_duration_seconds
                self.progress_update_callback(completed_percent)
            time.sleep(1)

    def get_latest_ms_progress(self):
        lines = self.output_file.readlines()

        if lines:
            for line in lines:
                if "out_time_ms" in line:
                    out_time_ms = line.split("=")[1]
                    return int(out_time_ms) / 1000000.0
        return None

    def stop(self):
        self.stop_event.set()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()


def name_normalize(name: str) -> str:
    name = re.sub(r'[?\\"%*:|<>]', "", name)
    name = re.sub(r"( [w,W]\s?\/\s?[o,O,0])", r" without", name)
    name = re.sub(r"( [w,W]\s?\/)", r" with", name)
    name = re.sub(r"(\d+)\s?\/\s?(\d+)", r"\1 of \2", name)
    name = re.sub(r"(\w+)\s?\/\s?(\w+)", r"\1 or \2", name)
    name = re.sub(r"\/", r"", name)

    lang = settings.config["reddit"]["thread"]["post_lang"]
    if lang:
        print_substep("Translating filename...")
        translated_name = ts.google(name, to_language=lang)
        return translated_name
    else:
        return name


def prepare_background(reddit_id: str, W: int, H: int) -> str:
    output_path = f"assets/temp/{reddit_id}/background_noaudio.mp4"

    return output_path


def make_final_video(
    number_of_clips: int,
    length: int,
    reddit_obj: dict,
    background_config: Tuple[str, str, str, Any],
):
    """Gathers audio clips, gathers all screenshots, stitches them together and saves the final video to assets/temp
    Args:
        number_of_clips (int): Index to end at when going through the screenshots'
        length (int): Length of the video
        reddit_obj (dict): The reddit object that contains the posts to read.
        background_config (Tuple[str, str, str, Any]): The background config to use.
    """
    # settings values
    W: Final[int] = int(settings.config["settings"]["resolution_w"])
    H: Final[int] = int(settings.config["settings"]["resolution_h"])

    reddit_id = re.sub(r"[^\w\s-]", "", reddit_obj["thread_id"])
    print_step("Creating the final video 🎥")

    background_clip = ffmpeg.input(prepare_background(reddit_id, W=W, H=H))

    # Gather all audio clips
    audio_clips = list()

    audio_clips = [
        ffmpeg.input(f"assets/temp/{reddit_id}/mp3/{i}.mp3")
        for i in range(number_of_clips)
    ]
    audio_clips.insert(0, ffmpeg.input(f"assets/temp/{reddit_id}/mp3/title.mp3"))

    audio_clips_durations = []

    for i in range(number_of_clips):
        audio_file_path = f"assets/temp/{reddit_id}/mp3/{i}.mp3"
        
        if os.path.exists(audio_file_path):
            audio_clips_durations.append(MP3(audio_file_path).info.length)

    audio_file_path = f"assets/temp/{reddit_id}/mp3/title.mp3"
    audio_clips_durations.insert(0, MP3(audio_file_path).info.length)

    console.log(f"[bold green] Video Will Be: {length} Seconds Long")

    screenshot_width = int((W * 45) // 100)
    audio = ffmpeg.input(f"assets/temp/{reddit_id}/audio.mp3")

    image_clips = list()

    image_clips.insert(
        0,
        ffmpeg.input(f"assets/temp/{reddit_id}/png/title.png")["v"].filter(
            "scale", screenshot_width, -1
        ),
    )

    current_time = 0

    for i in range(0, number_of_clips):

        print(i, "HERE", number_of_clips)

        image_clips.append(
            ffmpeg.input(f"assets/temp/{reddit_id}/png/comment_{i}.png")[
                "v"
            ].filter("scale", screenshot_width, -1)
        )
        background_clip = background_clip.overlay(
            image_clips[i],
            enable=f"between(t,{current_time},{current_time + audio_clips_durations[i]})",
            x="(main_w-overlay_w)/2",
            y="(main_h-overlay_h)/2",
        )
        current_time += audio_clips_durations[i]

    title = re.sub(r"[^\w\s-]", "", reddit_obj["thread_title"])
    idx = re.sub(r"[^\w\s-]", "", reddit_obj["thread_id"])
    title_thumb = reddit_obj["thread_title"]

    filename = f"{name_normalize(idx)[:251]}"
    subreddit = settings.config["reddit"]["thread"]["subreddit"]

    if not exists(f"./results/{subreddit}"):
        print_substep("The results folder didn't exist so I made it")
        os.makedirs(f"./results/{subreddit}")

    text = f"Background by {background_config[2]}"
    background_clip = ffmpeg.drawtext(
        background_clip,
        text=text,
        x=f"(w-text_w)",
        y=f"(h-text_h)",
        fontsize=12,
        fontcolor="White",
        fontfile=os.path.join("fonts", "Roboto-Regular.ttf"),
    )
    print_step("Rendering the video 🎥")

    from tqdm import tqdm

    pbar = tqdm(total=100, desc="Progress: ", bar_format="{l_bar}{bar}", unit=" %")

    def on_update_example(progress):
        status = round(progress * 100, 2)
        old_percentage = pbar.n
        pbar.update(status - old_percentage)

    path = f"results/{subreddit}/{filename}"
    path = path[:251]
    path = path + ".mp4"

    print(path)

    with ProgressFfmpeg(length, on_update_example) as progress:
        ffmpeg.output(
            background_clip,
            audio,
            path,
            f="mp4",
            **{
                "c:v": "h264",
                "b:v": "20M",
                "b:a": "192k",
                "threads": multiprocessing.cpu_count(),
            },
        ).overwrite_output().global_args("-progress", progress.output_file.name).run(
            quiet=True,
            overwrite_output=True,
            capture_stdout=False,
            capture_stderr=False,
        )

    old_percentage = pbar.n
    pbar.update(100 - old_percentage)
    pbar.close()

    print_step("Done! 🎉 The video is in the results folder 📁")