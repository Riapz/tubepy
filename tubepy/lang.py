import asyncio
import concurrent.futures
import json
import re
import urllib.request

import aiohttp
import requests  # this for testing purposes
from humanize.time import naturaldelta, precisedelta
from pytube import Playlist, YouTube
from version import __version__
from watchdog.events import FileSystemEventHandler

repo_link = "https://github.com/AlbertSolomon/tubepy"
app_info: dict = {
    "general_summary": "Quick Download: is an option that downloads' YouTube videos at the highest available resolution (MP4) quickly.\n\n Video: is an option for custom resolution and Please *note that some of the resolutions do not have audio (Quick Download is recomended).\n\n Audio: is an option for downloading the audio version of the video.",
    "about_app": f"Tubepy is a simple open source desktop app developed by Albert Solomon Phiri that allows easy downloading of Youtube Videos.\n\nTubepy is currently at version { __version__ } and is licensed under the MIT license hence you can modify and redistribute the software under the conditions of this license.\n\n CONTRIBUTIONS: Tubepy is a project which is tailored for the developer who are just getting started contributing to open source, it has a lot of 'good first issues' on Github.\n\n WANNA CONTRIBUTE ? : Interested contributors should follow this link to the repository { repo_link } or scan the QR CODE below, cant wait, happy coding and OOOH! dont forget to star ⭐ the project.\n\n LETS CODE TOGETHER !!!",
}

downloadstatus: dict = {
    "load": "loading... 😒",
    "download": "downloading... 😒",
    "audiodownload": "downloading audio 🎶 ...",
    "videodownload": "downloading video 📽️ ... ",
    "loadvideostreams": "loading video resolutions ... 🎥",
    "loadstreams": "loading audio frequencies... 🎶",
    "vstream_load_success": "video resolutions were successfully loaded 🎥",
    "stream_load_success": "audio frequencies were successfully loaded 🎶",
    "successful": "download successful 🥳",
    "unsuccessful": "download failed... 💔",
    "check_network": "checking network connection...🌐",
}

empty: dict = {
    "empty_location": " empty default location",
}

error_message: dict = {
    "invalid_length": "Invalid url length !. The URL length you have provided is invalid. Please try again 😥",
    "videoUnavailable": "Sorry, the video is not available at the moment. 💔",
    "url_issue": "The url you have provided is not valid. Please verify it and try again. 😊",
    "option_issue": "Please select an option... 😕",
    "network_error": "Sorry, bad network connection 🌐",
    "unavailable_options": "Options not available",
    "playlist_error": "Sorry, something went wrong during the download process 😥",
}

app_color: dict = {
    "primary": "#EECF89",
    "secondary": "#24DCA2",
    "extra_color": "#1C2331",
    "text_color": "#9B2E51",
    "hover_color": "#c9941d",
    "rightclick_menu_bg-color": "#565b5e",
}

event_color: dict = {
    "danger": "#AA1B48",
    "success": "#1BAA7D",
    "warning": "orange",
    "dark": "black",
}

widget_state: list = ["disabled", "normal"]

download_location = "~/Downloads"
default_download_location: dict = {"download_location": "~/Downloads"}


url_input = "Enter Youtube Video URL here 👉🏾: "
sample_url = "https://www.youtube.com/shorts/mBqK_-L-GVp"  # "https://www.youtube.com/shorts/mBqK_-L-PVg" (this url works)


# refactoring for reading for reading from config.json file
def read_config_file():
    try:
        with open("utilities/config.json", "r") as config_location:
            location = json.load(config_location)

    except FileNotFoundError:
        with open("utilities/config.json", "w") as config_file:
            json.dump(default_download_location, config_file, indent=4)

        with open("utilities/config.json", "r") as config_location:
            location = json.load(config_location)

        return location
    return location


class CodeChangeHandler(FileSystemEventHandler):
    """This is a handler for the code change event during development."""

    def __init__(self, callback, exclude_dir=None, exclude_file=None):
        super().__init__()
        self.callback = callback
        self.exclude_dir = exclude_dir
        self.exclude_file = exclude_file

    def on_any_event(self, event):
        if (
            event.is_directory
            and self.exclude_dir
            and event.src_path.startswith(self.exclude_dir)
        ):
            return
        if event.src_path == self.exclude_file:
            return
        if event.event_type in ["modified", "created", "deleted"]:
            self.callback()


# function from https://github.com/JNYH/pytube/blob/master/pytube_sample_code.ipynb
def clean_filename(name) -> str:
    """Ensures each file name does not contain forbidden characters and is within the character limit"""
    # For some reason the file system (Windows at least) is having trouble saving files that are over 180ish
    # characters.  I'm not sure why this is, as the file name limit should be around 240. But either way, this
    # method has been adapted to work with the results that I am consistently getting.

    forbidden_chars = "\"*\\/'.|?:<>"
    filename = (
        ("".join([x if x not in forbidden_chars else "#" for x in name]))
        .replace("  ", " ")
        .strip()
    )
    if len(filename) >= 176:
        filename = filename[:170] + "..."
    return filename


def validate_youtube_url(url) -> bool:
    "This makes sure the url provided is valid and acceptable. No one likes regex so i asked CHATGPT 🤣."

    # https://youtu.be/KR22jigJLok
    youtube_regex = re.compile(
        r"((https?://)?(www\.)?"
        r"(youtube|youtu|youtube-nocookie)\.(com|be)/"
        r"(watch\?v=|embed/|v/|.+\?v=|shorts/)?([^&=%\?]{11}))"
        r"|(youtu\.be/[^&=%\?]{11})"
    )

    acceptable_urls = [
        "youtube.com/",
        "www.youtube.com/",
        "m.youtube.com/",
        "youtu.be/",
        "youtube-nocookie.com/",
    ]

    return youtube_regex.search(url) is not None or any(
        domain in url for domain in acceptable_urls
    )


# dotbe: str = "https://youtu.be/mVX3Z46iYTQ"
# print(validate_youtube_url(dotbe))


def file_existance(youtube_url) -> int:
    """This function is a available for testing purposes, thus to compare
    it's result with the search_file_Availability function."""

    request = requests.get(youtube_url, allow_redirects=False)
    return request.status_code


async def search_file_Availability(youtube_url) -> int:
    """The name of the function speaks volumes of it self, it does what it says it does 🤣."""

    if "youtu.be/" in youtube_url:
        youtudotbe_url = youtube_url.replace("youtu.be/", "www.youtube.com/watch?v=")
        youtube_url = youtudotbe_url

    async with aiohttp.ClientSession() as session:
        async with session.get(youtube_url, allow_redirects=False) as response:
            return response.status


async def file_verification(youtube_url) -> bool:
    """This relys on the search_file_availability function and the validate_youtube_url function to make sure the Youtube file is available."""

    validatd_url = validate_youtube_url(youtube_url)
    status = await search_file_Availability(youtube_url) if validatd_url else None

    if status == 200:
        return True
    return False


def youtubefile(function):
    """This is a decorator that returns a Youtube Object, why? because it was supposed to make the code DRY 💔."""

    def wrapper(youtube_url):
        youtube_file = YouTube(youtube_url)
        return function(youtube_file)

    return wrapper


# adding stream codes to a list
@youtubefile
async def add_audio_stream_codes(youtube_file) -> list:
    """This function tries to extract the audio stream codes from the youtube url.
    it returns a list of audio stream codes. Its simply a list of lists, it has two indices and this is it's format:

    stream[abr][itag] where
        ::streams[0] returns a list of audio abr.
        ::streams[1] returns a list of audio stream itags from a Stream object.

    :fulldetails is for testing purposes ..."""

    streams: list = []
    itag: list = []
    abr: list = []

    fulldetails: list = []  # for testing purposesyyy
    available_audiofiles = youtube_file.streams.filter(only_audio=True)

    for available_audiofile in available_audiofiles:
        itag.append(available_audiofile.itag)
        abr.append(available_audiofile.abr)
        # fulldetails.append(available_audiofile)

    streams.append(abr)
    streams.append(itag)
    # streams.append(fulldetails)
    return streams


@youtubefile
async def add_video_stream_code(youtube_file) -> list:
    """
    The use of a youtubefile decorator does not make this function any special, this gets video itags and video resolution from a Stream object.
    This is also a list of lists with two indices and should be implemented in the following format:
        :: stream[0] -> return list of video resolution.
        :: stream[1] -> return list of itags.
    """

    streams: list = []
    itag: list = []
    video_resolution: list = []

    available_videofiles = youtube_file.streams.filter(file_extension="mp4")

    for available_videofile in available_videofiles:
        itag.append(available_videofile.itag)
        resolution = available_videofile.resolution
        codec = available_videofile.video_codec

        if resolution != None:
            video_resolution.append(f"{resolution} | { codec }")

    streams.append(video_resolution)
    streams.append(itag)
    return streams


async def check_internet_connection(youtube_url) -> bool:
    """
    Check if an internet connection is available by attempting to open a URL within a specified timeout.

    Parameters:
    youtube_url (str): The URL to check for internet connection.

    Returns:
    bool: True if the URL can be opened within the timeout, False otherwise.

    Raises:
    None.

    Example:
    >>> is_connected = asyncio.run( check_internet_connection("https://www.youtube.com/") )
    >>> print(is_connected)
    True
    """

    try:
        await asyncio.to_thread(urllib.request.urlopen, youtube_url, timeout=5)
        return True
    except (urllib.error.URLError, asyncio.TimeoutError):
        return False


async def downloadfile_details(youtube_file) -> dict:
    """
    This function retrieves relevant information from a YouTube object.

    Returns:
    dict: A dictionary containing the details of the `youtube_file` object.

    Raises:
    None.

    Example:
    >>> file_details = asyncio.run( downloadfile_details(youtube_url) )
    >>> print(file_details)
    {'title': 'Rick Astley - Never Gonna Give You Up (Video)', 'author': 'Rick Astley', 'length': '00:03:33', 'thumbnail': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg', 'views': '1,373,364,201', 'date': '12 years ago'}
    """

    title = youtube_file.title
    author = youtube_file.author
    video_description = youtube_file.description
    video_info = youtube_file.vid_info

    lenght = youtube_file.length
    thumbnail = youtube_file.thumbnail_url
    channel = youtube_file.channel_url
    views = youtube_file.views

    upload_date = youtube_file.publish_date
    file_info: dict = {
        "title": title,
        "author": author,
        # "description": video_description,
        # "info": video_info,
        "length": precisedelta(
            lenght, suppress=["seconds", "milliseconds", "microseconds"]
        ),
        "thumbnail": thumbnail,
        # "channel": channel,
        "views": views,
        "date": precisedelta(
            upload_date
        ),  # naturaldelta(upload_date, months=True, minimum_unit='hours')
    }

    return file_info


async def playlist_details(youtube_url) -> dict:
    """
    Retrieves basic information about a YouTube playlist.

    Args:
        youtube_url (str): A string representing the URL of the YouTube playlist.

    Returns:
        dict: A dictionary containing the following keys and their corresponding values:
            - "title": A string representing the title of the playlist.
            - "length": An integer representing the number of videos in the playlist.
            - "views": An integer representing the total number of views of the playlist.
            - "url": A string representing the URL of a sample video from the playlist.
    """

    sample_playlist_url: str = ""

    if "playlist" in youtube_url:
        playlist = Playlist(youtube_url)
        # do a lazy loop
        for sample_url in playlist.video_urls[:1]:
            sample_playlist_url = sample_url

        playlist_info = await downloadfile_details(sample_playlist_url)
        playlist_info["title"] = playlist.title
        playlist_info["length"] = playlist.length
        playlist_info["views"] = playlist.views

    return playlist_info

def onfailure_decorator(functione):
    def wrapper(url, on_progress=None):
        try:
            return function(url,)
        except Exception as the_error:
            print("download failed...😥")
            print(the_error)

    return wrapper

"""

@ ideas :::: write a decorator that registers errors to some global variable or file
:: and write code that monitor this file, and print or displays errors registered in this files/global variable and this should happen in real time.    

"""
def on_download_failure_decorator(error_function=None):
    def onfailure_decorator(function):
        def wrapper(url, on_progress=None):
            try:
                if on_progress is not None:
                    return function(url, on_progress=on_progress)
                else:
                    return function(url,)
            except Exception as the_error:
                if error_function is not None:
                    app=""
                    error_function(app, the_error, event_color.get("danger"))
                else:
                    print(f"download failed....\n error::> {the_error} ")
        return wrapper
    return onfailure_decorator
