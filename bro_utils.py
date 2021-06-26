# FourthBrother allows to use Telegram Bot API to control you Raspberry Pi
# Copyright (C) 2021 Pablo del Hoyo Abad <pablodelhoyo1314@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
