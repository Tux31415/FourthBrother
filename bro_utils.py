import time
import subprocess
import os

FFMPEG_COMMAND = "ffmpeg -framerate {} -i pipe: -c:v copy {}"

def convert_to_mp4(stream, framerate):
    """ Puts h264 video stream in a mp4 container, which is the one Telegram supports
    Framerate is necessary because that information is not held by a video codec 
    stream must be a byte object"""

    # I use unix time as the name of the file to avoid having two mp4 with the same name
    # This could happen because once during processing, another video can be recorded 
    timestamp = int(time.time())
    file_name = f"{timestamp}.mp4"
    command = FFMPEG_COMMAND.format(framerate, file_name).split()

    subprocess.run(command, input=stream, stderr=subprocess.DEVNULL)

    mp4_container_stream = None

    try:
        mp4_container_stream = open(file_name, "rb")
        return mp4_container_stream
    except IOError as exc:
        if mp4_container_stream:
            mp4_container_stream.close()
        raise exc
    finally:
       if os.path.isfile(file_name):
           os.remove(file_name)

    return None
