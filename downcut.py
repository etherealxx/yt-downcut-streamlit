import streamlit as st
# from streamlit_extras.row import row 
import os
import yt_dlp
import pandas as pd
from pandas import json_normalize
import platform
import re
import ffmpy
import subprocess
from mimetypes import guess_type
import time
from datetime import datetime, timedelta

class CustomError(Exception):
    def __init__(self, message):
        super().__init__(message)

def sanitize(text, mode=""):
    if mode == "filename":
        restricted_characters = r'<>:"/\|?*'
        text = re.sub(r'[' + re.escape(restricted_characters) + ']', '_', text)
        text = re.sub(r'(?:[. ]+$|^ +)', '', text)
        text = text.replace('/', '_').replace('\0', '_')
        text = text[:255]  # Truncate to 255 characters, which is the max length in NTFS.
        output_string = re.sub(r'(^[. ]+|[. ]+$)', '', text)
    else:
        pattern = re.compile(r'\x1B\[[0-9;]*m')
        output_string = re.sub(pattern, '', text)
    return output_string

if platform.system() == 'Windows':
    downloadpath = os.path.expanduser("~\Downloads")
else:
    downloadpath = os.path.expanduser("~/Downloads")

st.title("YouTube Video Downloader")

# Textbox to input the YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:")
st.caption("Example: https://www.youtube.com/watch?v=chh1ZCCsUGk , https://www.youtube.com/watch?v=vaNa34yEEWs")
progress = st.empty()

# format_id = st.text_input("Enter Preferred Format ID:")
if 'idlistvideo' not in st.session_state:
    id_list_video = st.empty # st.selectbox("Enter Preferred Format ID of video stream: (Empty)", [""], label_visibility='collapsed')
else:
    id_list_video = st.selectbox("Enter Preferred Format ID of video stream:", options=st.session_state['idlistvideo'], label_visibility='visible')
# Button to trigger the download
if 'mode' not in st.session_state:
    st.session_state.mode = 'video'

if 'successvideopath' not in st.session_state:
    st.session_state.successvideopath = ""

if 'successaudiopath' not in st.session_state:
    st.session_state.successaudiopath = ""

def changemode():
    st.session_state.mode = modechooser

modechooser = st.radio(
    "Set download mode",
    ["Video", "Audio"],
    horizontal=True,
    on_change=changemode
)

st.text(f"mode: {modechooser}")

col1, col2 = st.columns(2)
# buttonrow = row(2, vertical_align="center")
# format_check = buttonrow.button("Check Format")
format_check = col1.button("Check Format")
col2.button("OK")

if format_check:
    ydl_opts = {
    'quiet': True  # Suppress youtube-dl output
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
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
                'url', 'width', 'height', 'rows', 'columns', 'fragments',
                'aspect_ratio', 'resolution', 'http_headers.User-Agent', 'http_headers.Accept',
                'http_headers.Accept-Language', 'http_headers.Sec-Fetch-Mode', 'asr', 'source_preference',
                'audio_channels', 'quality', 'has_drm', 'language', 'language_preference',
                'preference', 'dynamic_range', 'downloader_options.http_chunk_size',
                'format_index', 'manifest_url'
            ]

            if modechooser == "Video":
                # columns_to_omit.append('acodec')
                df = json_normalize(video_formats).drop(columns=columns_to_omit)
                # id_list_video = st.selectbox("Enter Preferred Format ID of video stream: (updated)", options=videolist, label_visibility='visible')

            else:
                # columns_to_omit.append('vcodec')
                df = json_normalize(audio_formats).drop(columns=columns_to_omit)

            videolist = df['format_id'].tolist()    
            st.session_state['idlistvideo'] = videolist
            st.dataframe(df)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            print(f"Error: {str(e)}")

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
        # try:
        st.info(f"Downloading video from {video_url}...")

        def download_progress_hook(d):
            global progress
            if d['status'] == 'downloading':
                percent = d['_percent_str']
                speed = d['_speed_str']
                eta = d['_eta_str']
                progress.markdown(sanitize(f"Downloading: {percent} at {speed}, ETA: {eta}"))
                # sys.stdout.flush()
            elif d['status'] == 'finished':
                pass
                # sys.stdout.write('\n')
            elif d['status'] == 'error':
                progress.markdown(sanitize(f"Error: {d['error']}"))
                # sys.exit(1)

        ydl_opts = {
            'progress_hooks': [download_progress_hook],
            'outtmpl': os.path.join(downloadpath, '%(title)s.%(ext)s')
        }

        # print(ydl_opts['outtmpl'])

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            formats = info_dict.get('formats', [])

            if id_list_video:
                # print("picking the chosen format")
                ydl_opts['format'] = id_list_video
            else:
                # print("picking the highest quality format")   
                highest_id_format = max(formats, key=lambda x: int(x['format_id']))

                # # Update the 'format' option with the highest format ID
                ydl_opts['format'] = highest_id_format['format_id']

            # if modechooser == "Video":
            #     ydl_opts['format'] = 'bestvideo'
            # else:
            #     ydl_opts['format'] = 'bestvideo'

            # print(f"format: {ydl_opts['format']}")
            chosen_format = next((f for f in formats if f['format_id'] == ydl_opts['format']), None)
            # print(f"chosen_format: {chosen_format}")
            # print("format: " + str(ydl_opts['format']))
            # if 'outtmpl' in ydl_opts:
            #     del ydl_opts['outtmpl']

            # ydl_opts['outtmpl'] = os.path.join(downloadpath, '%(title)s.' + chosen_format['ext'])
            downloaded_file_path = os.path.join(downloadpath, sanitize(info_dict['title'], "filename") + f'_{modechooser}.' + chosen_format['ext'])
            # print(downloaded_file_path +"\n"+str(ydl_opts['outtmpl']))
            ydl_opts['outtmpl']['default'] = downloaded_file_path
            # print(str(ydl_opts['outtmpl']))
            
            if os.path.exists(downloaded_file_path):
                os.remove(downloaded_file_path)

            # command = [
            #     "yt-dlp",
            #     "-f",
            #     ydl_opts['format'],
            #     "-o",
            #     downloaded_file_path,
            #     video_url
            # ]

            # # Create a subprocess to run the command
            # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Command to run with subprocess
            command = 'yt-dlp -f '+ ydl_opts['format'] +' -o "' + downloaded_file_path +'" "'+ video_url +'"'

            # Create a subprocess to run the command with shell=True
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Read and print the output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # print(output.strip())
                    progress.markdown(sanitize(output.strip()))

            # Wait for the process to finish
            process.wait()

            # ydl.download([video_url])
            if process.returncode == 0:
                st.success(f"Video downloaded successfully. The file is saved at: {downloaded_file_path}")
                os.utime(downloaded_file_path, (os.path.getatime(downloaded_file_path), time.time()))
                if modechooser == "Video":
                    st.session_state.successvideopath = downloaded_file_path
                else:
                    st.session_state.successaudiopath = downloaded_file_path
            else:
                st.warning(f"Video has problem when downloading. Error code: {process.returncode}")
        # except Exception as e:
        #     st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please enter a valid YouTube video URL.")

def determinetemplate(boxtype):
    if boxtype == "Video":
        return st.session_state.successvideopath if st.session_state.successvideopath else ""
    else:
        return st.session_state.successaudiopath if st.session_state.successaudiopath else ""

st.write("Cutter")
cutter_videopath = st.text_input("Video path", value=determinetemplate("Video"))
cutter_audiopath = st.text_input("Audio path", value=determinetemplate("Audio"))
cutter_starttime = st.text_input("Start Time")
cutter_endtime = st.text_input("End Time")
cutter_progress = st.empty()
cutter_button = st.button("Cut Now")

def modifiedname(path, modifier, modifiedextension=""):
    # Split the file path into directory and filename
    directory, filename = os.path.split(path)
    
    # Split the filename into the name and extension
    name, extension = os.path.splitext(filename)
    
    if modifiedextension:
        extension = f".{modifiedextension}"

    # Add "_copy" to the filename
    new_filename = f"{name}_{modifier}{extension}"
    
    # Create the new file path
    new_file_path = os.path.join(directory, new_filename)
    
    return new_file_path

if cutter_button:
    # # Cut the video
    output_video = modifiedname(cutter_videopath, "cutted")

    # ff = ffmpy.FFmpeg(
    #     inputs={cutter_videopath: ['-y', '-ss', cutter_starttime, '-t', cutter_endtime]},
    #     outputs={output_video: ['-c:v', 'copy']}
    # )
    # ff.run()

    # # Cut the audio
    output_audio = modifiedname(cutter_audiopath, "cutted", "m4a") # aac

    # ff = ffmpy.FFmpeg(
    #     inputs={cutter_audiopath: ['-y', '-ss', cutter_starttime, '-t', cutter_endtime]},
    #     outputs={output_audio: ['-c:a', 'copy']}
    # )
    # ff.run()

    # # Combine the cut video and audio
    final_output = modifiedname(cutter_videopath, "final")

    # ff = ffmpy.FFmpeg(
    #     inputs={output_video: None, output_audio: None},
    #     outputs={final_output: ['-y', '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental']}
    # )
    # # ff.run()

    # # Redirect stdout and stderr to subprocess.PIPE
    # process = ff.run(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def runffmpeg(command):
        global cutter_progress
        print(command)
        # process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        # while True:
        #     output = process.stdout.readline()
        #     if output == '' and process.poll() is not None:
        #         break
        #     if output:
        #         # print(output.strip())
        #         cutter_progress = st.markdown(sanitize(output.strip()))
        #         print(output.strip())
        while True:
            line = process.stdout.readline()
            if not line:
                break
            cutter_progress = st.empty()
            cutter_progress = st.markdown(sanitize(line.strip()))
            print(line, end='')

    def timeformat(format):
        return "00:" + format if format.count(":") == 1 else format
    
    def duration(start_time, end_time):
        time_format = "%H:%M:%S"
        
        start_datetime = datetime.strptime(timeformat(start_time), time_format)
        end_datetime = datetime.strptime(timeformat(end_time), time_format)

        duration = end_datetime - start_datetime
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours:02}:{minutes:02}:{seconds:02}"

    print("\nDoing the ffmpeg operations...")
    try:
        if os.path.exists(cutter_videopath):
            command = f"ffmpeg -y -ss {timeformat(cutter_starttime)} -i \"{cutter_videopath}\" -t {duration(cutter_starttime, cutter_endtime)} -c:v copy \"{output_video}\""
            runffmpeg(command) # cut video
        else:
            raise CustomError(f"Error: Video path doesn't exist: {cutter_videopath}")
        
        if os.path.exists(cutter_audiopath):
            command = f"ffmpeg -y -ss {timeformat(cutter_starttime)} -i \"{cutter_audiopath}\" -t {duration(cutter_starttime, cutter_endtime)} -c:a aac \"{output_audio}\""
            runffmpeg(command) # cut audio
        else:
            raise CustomError(f"Error: Audio path doesn't exist: {cutter_audiopath}")
        if os.path.exists(output_video) and os.path.exists(output_video):
            command = f"ffmpeg -i \"{output_video}\" -i \"{output_audio}\" -c:v copy -c:a copy -y \"{final_output}\""
            runffmpeg(command) # merge video and audio
        else:
            raise CustomError(f"Error: Either the video or audio cutting process is failed. Can't proceed to merging.")

        if os.path.exists(final_output):
            st.write(f"Operation success: {final_output}")
            os.remove(output_video)
            os.remove(output_audio)
            with open(final_output, "rb") as file:
                st.download_button('Download final video', file, os.path.basename(final_output),
                                guess_type(os.path.basename(final_output))[0])
        else:
            st.write(f"Somehow operation failed")
    except Exception as e:
        st.error(str(e))

    # # Create a while loop to capture and print the output in real time
    # while True:
    #     # stdout_line = process[0].readline()
    #     # stderr_line = process[1].readline()
    #     stdout_line = process[0].decode('utf-8').strip()
    #     stderr_line = process[1].decode('utf-8').strip()

    #     if not stdout_line and not stderr_line:
    #         break

    #     if stdout_line:
    #         progress.markdown(sanitize(stdout_line.decode('utf-8').strip()))
    #     # if stderr_line:
    #     #     print("FFmpeg stderr: " + stderr_line.decode('utf-8').strip())

    # # Wait for the process to finish
    # process.wait()

makedownload_button = st.button("Make Download Button")
makedownload_textbox = st.text_input("Final video path")
if makedownload_button:
    if os.path.exists(makedownload_textbox):
        with open(makedownload_textbox, "rb") as file:
            st.download_button('Download video', file, os.path.basename(makedownload_textbox),
                               guess_type(os.path.basename(makedownload_textbox))[0])