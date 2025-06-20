import json
import subprocess

import yt_dlp


def get_duration_yt_dlp(url):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "no_call_home": True,
        "no_check_certificate": True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            dictMeta = ydl.extract_info(url, download=False, )
            return dictMeta['duration']
    except Exception as e:
        raise Exception(f"Failed getting duration from the following video/audio url/path using yt_dlp. {url} {e.args[0]}")


def get_duration_ffprobe(signed_url):
    try:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-i",
            signed_url
        ]
        output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if output.returncode != 0:
            return None, f"Error executing command using ffprobe. {output.stderr.strip()}"

        metadata = json.loads(output.stdout)
        duration = float(metadata["format"]["duration"])
        return duration, ""
    except Exception as e:
        print("Failed getting the duration of the asked ressource", e.args[0])
    return None, ""


def get_asset_duration(url, isVideo=True):
    if ("youtube.com" in url):
        if not isVideo:
            url, _ = getYoutubeAudioLink(url)
        else:
            url, _ = getYoutubeVideoLink(url)
    # Trying two different method to get the duration of the video / audio
    duration, err_ffprobe = get_duration_ffprobe(url)
    if duration is not None:
        return url, duration

    duration = get_duration_yt_dlp(url)
    if duration is not None:
        return url, duration
    print(err_ffprobe)
    raise Exception(f"The url/path {url} does not point to a video/ audio. Impossible to extract its duration")


def getYoutubeAudioLink(url):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "no_call_home": True,
        "no_check_certificate": True,
        "format": "bestaudio/best"
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            dictMeta = ydl.extract_info(url, download=False)
            return dictMeta['url'], dictMeta['duration']
    except Exception as e:
        print("Failed getting audio link from the following video/url", e.args[0])
        return None


def getYoutubeVideoLink(url):
    """
    Extracts the video URL from a YouTube URL using yt_dlp.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "no_call_home": True,
        "no_check_certificate": True,
        "format": "bestvideo+bestaudio/best"  # or "best" for the best quality
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            dictMeta = ydl.extract_info(url, download=False)
            return dictMeta['url'], dictMeta['duration']
    except Exception as e:
        print("Failed getting video link from the following video/url", e.args[0])
        return None, None
