# FourthBrother allows to use Telegram Bot API to control your Raspberry Pi
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

import logging
import threading
import time
from io import BytesIO

from gpiozero import LED, MotionSensor
from picamera import PiCamera

from decouple import config
from telegram.ext import Updater, CommandHandler

import bro_handlers
import bro_utils
from negative_logic_relay import NegativeLogicRelay


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TOKEN = config("TOKEN")
GROUP_CHAT_ID = config("GROUP_CHAT_ID", cast=int)

# It is important that in the .env file, in order to specify
# the pin associated to each device calling the env variable
# following the format: '{DEVICE_NAME}_PIN'
DEVICES_NAMES = ["PIR_SENSOR", "LED", "RELAY"]

CAMERA_FRAMERATE = config("CAMERA_FRAMERATE", default=30, cast=int)

def generate_pin_dict():
    """ Returns a dict where the key is the device name
    and the value the pin which is connected to"""
    pins = {}
    for device_name in DEVICES_NAMES:
        pins[device_name] = config(f"{device_name}_PIN", cast=int)

    return pins


class FourthBrother:

    def __init__(
        self, 
        token, 
        authorized_chat, 
        pin_dict, 
        camera_framerate=CAMERA_FRAMERATE,
        camera_resolution=(576, 288),
        flip=(False, False)
    ):
        # telegram api stuff
        self.__updater = Updater(token)
        self.__dispatcher = self.__updater.dispatcher

        # only one chat is allowed to talk to the bot. This way, bro knows where
        # to send a message when the value of a sensor changes
        self.__authorized_chat = authorized_chat

        # devices 
        self.led = LED(pin_dict["LED"])
        self.pir_sensor = MotionSensor(pin_dict["PIR_SENSOR"])
        self.relay = NegativeLogicRelay(pin_dict["RELAY"])

        self.camera = PiCamera(framerate=camera_framerate, resolution=camera_resolution)
        self.camera.vflip, self.camera.hflip = flip

        # I use Event() to ensure atomicity. Moreover, there is not a lof overhead in using it
        self.using_camera = threading.Event()
        self.pir_activated = False
        self.last_time_pir = 0
        self.camera_framerate = camera_framerate


    def add_handler_to_device(self, attr_device_name, **events):
        """ Adds an event handler to a device. The callback receives a
            reference to this class 
            NOTE: attr_device_name is the name the object (representing a device)
            has in this class """

        device = getattr(self, attr_device_name)
        for event_name, event_handler in events.items():
            if not hasattr(device, event_name):
                raise AttributeError(f"{type(device)} does not have the event '{event_name}'")

            setattr(device, event_name, lambda: event_handler(self))

    def add_command(self, name, callback, run_async=True):
        """ Registers the callback for a specfied command (messages starting
            with '/'). The callback is only called if the message comes from 
            an authorized chat
            
            NOTE: callback receives a reference of the FourthBrother object wich
            registered it """
            
        def command_wrapper(update, context, *args, **kwargs):
            if update.message.chat_id == self.__authorized_chat:
                callback(self, update, context, *args, **kwargs)
            
            # TODO: else, register somewhere that someone has tried to 
            # talk to FourthBrother from an unauthorized chat

        self.__dispatcher.add_handler(CommandHandler(name, command_wrapper, run_async=run_async))

    def start_polling(self, timeout=10, courtesy_time=2):
        """ Gets new updates by the long polling method
        timeout: maximum time until Telegram servers return the reply for 'getUpdates' request
        courtesy_time: extra time to wait before raising a Timeout exception """

        self.__updater.start_polling(timeout=timeout, read_latency=courtesy_time)

        # waits until all threads have finished their tasks before exiting completely
        self.__updater.idle()
    

    def get_image_stream(self):
        """ Takes a photo and returns a bytes object representing the image """

        stream = BytesIO()
        self.camera.capture(stream, "png")
        stream.seek(0)
        return stream

    def get_video_stream(self, video_duration):
        """ Records a video and returns the byte stream """

        stream = BytesIO()
        self.camera.start_recording(stream, format="h264", quality=23)
        self.camera.wait_recording(video_duration)
        self.camera.stop_recording()
        stream.seek(0)
        return stream

    def record_and_send_video(self, duration, inform=True):
        """ Records and sends a video with the specified duration. 
        If inform is True then telegram messages will be sent telling the stage of the 
        process it is i.e (recording, processing, etc)"""

        if inform:
            self.send_message(f"La grabación durará {duration} segundos")
            
        with self.get_video_stream(duration) as video_stream:
            if inform:
                self.send_message("Se ha terminado la grabación. Iniciando procesamiento")
            
            with bro_utils.convert_to_mp4(video_stream.read(), self.camera_framerate) as mp4_stream:
                self.send_video(mp4_stream)        

    def send_message(self, message, *args, **kwargs):
        """ Sends a message to the chat which is authorized to talk to """

        self.__updater.bot.send_message(self.__authorized_chat, message, *args, **kwargs)
    
    def send_photo(self, photo, *args, **kwargs):
        """ Sends a photo (stream of bytes) to the chat which is authorized to talk to """

        self.__updater.bot.send_photo(self.__authorized_chat, photo, *args, **kwargs)

    def send_video(self, video, *args, **kwargs):
        """ Sends a video (stream of bytes) to the chat which is authorized to talk to """

        self.__updater.bot.send_video(self.__authorized_chat, video, *args, **kwargs)


def main():
    pin_dict = generate_pin_dict()
    bro = FourthBrother(TOKEN, GROUP_CHAT_ID, pin_dict, flip=(True, True))

    bro.add_command("relay", bro_handlers.relay_command) 
    bro.add_command("foto", bro_handlers.photo_command) 
    bro.add_command("video", bro_handlers.video_command) 
    bro.add_command("sensor", bro_handlers.sensor_command)

    bro.add_handler_to_device("pir_sensor", when_activated=bro_handlers.movement_handler)

    bro.start_polling(timeout=15)

    # TODO: polling at night is nonse. Establish
    # an interval of time when the bot does not poll? 


if __name__ == "__main__":
    main()
