import streamlit as st
import os
from pytube import YouTube
import yt_dlp
import sys
import pandas as pd
from pandas import json_normalize

downloadpath = os.path.expanduser("~\Downloads")

st.title("YouTube Video Downloader")

# Textbox to input the YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:")
st.caption("Example: https://www.youtube.com/watch?v=chh1ZCCsUGk")
progress = st.empty()
format_id = st.text_input("Enter Preferred Format ID:")
# Button to trigger the download
if st.button("Check Format"):
    ydl_opts = {
    'quiet': True  # Suppress youtube-dl output
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        formats = info_dict.get('formats', [])

        # def parse_format_id(format):
        #     try:
        #         return int(format['format_id'])
        #     except (ValueError, TypeError):
        #         return 0

        video_formats = [f for f in formats if 'acodec' in f and f['acodec'] == 'none']
        audio_formats = [f for f in formats if 'vcodec' in f and f['vcodec'] == 'none']

        columns_to_omit = [
            'acodec', 'url', 'width', 'height', 'rows', 'columns', 'fragments',
            'aspect_ratio', 'resolution', 'http_headers.User-Agent', 'http_headers.Accept',
            'http_headers.Accept-Language', 'http_headers.Sec-Fetch-Mode', 'asr', 'source_preference',
            'audio_channels', 'quality', 'has_drm', 'language', 'language_preference',
            'preference', 'dynamic_range', 'downloader_options.http_chunk_size',
            'format_index', 'manifest_url'
        ]

        df = json_normalize(video_formats).drop(columns=columns_to_omit)

        st.dataframe(df)
        # if video_formats:
        #     highest_video_format = max(video_formats, key=parse_format_id)
        # else:
        #     highest_video_format = None

        # if audio_formats:
        #     highest_audio_format = max(audio_formats, key=parse_format_id)
        # else:
        #     highest_audio_format = None

if st.button("Download"):
    # if video_url:
    #     try:
    #         st.info(f"Downloading video from {video_url}...")

    #         # Creating a YouTube object
    #         yt = YouTube(video_url)

    #         # Select the highest resolution stream (first stream)
    #         video_stream = yt.streams.filter(file_extension="mp4").get_highest_resolution()

    #         # Download the video
    #         video_stream.download(output_path=downloadpath, filename=f"{yt.title}.{video_stream.subtype}")

    #         st.success(f"Video downloaded successfully as {yt.title}.mp4")
    #     except Exception as e:
    #         st.error(f"An error occurred: {str(e)}")
    # else:
    #     st.warning("Please enter a valid YouTube video URL.")
    if video_url:
        try:
            st.info(f"Downloading video from {video_url}...")

            def download_progress_hook(d):
                global progress
                if d['status'] == 'downloading':
                    percent = d['_percent_str']
                    speed = d['_speed_str']
                    eta = d['_eta_str']
                    progress.markdown(f"Downloading: {percent} at {speed}, ETA: {eta}")
                    # sys.stdout.flush()
                elif d['status'] == 'finished':
                    pass
                    # sys.stdout.write('\n')
                elif d['status'] == 'error':
                    progress.markdown(f"Error: {d['error']}")
                    # sys.exit(1)

            ydl_opts = {
                'progress_hooks': [download_progress_hook],
                'outtmpl': os.path.join(downloadpath, '%(title)s.%(ext)s'),
            }
            if format_id:
                ydl_opts['format'] = format_id
            else:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video_url, download=False)
                    formats = info_dict.get('formats', [])
                    
                    highest_id_format = max(formats, key=lambda x: int(x['format_id']))

                # # Update the 'format' option with the highest format ID
                ydl_opts['format'] = highest_id_format['format_id']

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            st.success(f"Video downloaded successfully")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please enter a valid YouTube video URL.")

st.write("Note: This app only works with public YouTube videos.")
