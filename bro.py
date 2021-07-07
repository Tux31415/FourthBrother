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
from telegram.ext import (Updater, CommandHandler, 
                CallbackQueryHandler, ConversationHandler)
from telegram.error import NetworkError

import bro_handlers
import bro_utils
import menu
import constants
from negative_logic_relay import NegativeLogicRelay


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# It is important that in the .env file, in order to specify
# the pin associated to each device calling the env variable
# following the format: '{DEVICE_NAME}_PIN'
DEVICES_NAMES = ["PIR_SENSOR", "RELAY_A", "RELAY_B"]

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
        camera_framerate=constants.CAMERA_FRAMERATE,
        camera_resolution=(576, 288),
        rotation=0
    ):
        # telegram api stuff
        self.__updater = Updater(token)
        self.__dispatcher = self.__updater.dispatcher

        # only one chat is allowed to talk to the bot. This way, bro knows where
        # to send a message when the value of a sensor changes
        self.__authorized_chat = authorized_chat

        # the process of changing mode must be atomic to avoid possible shortcircuits
        self.__switching_mode_lock = threading.Lock()

        self._menu_message = None

        self.pir_sensor = MotionSensor(pin_dict["PIR_SENSOR"])

        # when this relay is on, the lamp acts as if there were no pir sensor
        self.relay_normal = NegativeLogicRelay(pin_dict["RELAY_A"])
        self.relay_manual = NegativeLogicRelay(pin_dict["RELAY_B"])

        self.camera = PiCamera(framerate=camera_framerate, resolution=camera_resolution)
        self.camera.rotation = rotation

        self.camera_lock = threading.Lock()
        self.pir_activated = False

        # If this is true, then the lamp will be on for an specified amount of time when the pir sensor
        # detects movement
        self.movement_activated = False
        self.is_normal_mode = True
        self.last_time_pir = 0


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

    def add_command(self, name, callback, run_async=True, end_menu=True):
        """ Registers the callback for a specfied command (messages starting
            with '/') If 'end_menu' is true, then the menu will be sent after
            the callback associated with this handler has ended.
            NOTE: callback receives a reference of the FourthBrother object wich
            registered it """

        def command_wrapper(update, context):
            if update.message.chat_id == self.__authorized_chat:
                callback(self, update, *context.args)
                if end_menu:
                    self.send_menu()
            
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
    
    def change_to_normal_mode(self):
        """ Switches the relays in such a way that the lamps acts as if there were no pir sensor"""

        with self.__switching_mode_lock:
            if not self.is_normal_mode:
                self.relay_manual.off()
                # leave enough time for the relay to switch state. We don't want a shortcircuit
                time.sleep(constants.DELAY_RELAYS)
                self.relay_normal.off()
                self.is_normal_mode = True

    # TODO: make sure to gracefully change to manual mode when exiting in case
    # it is not in that mode
    def change_to_manual_mode(self):
        """ Switches the relays in such a way that the lamp activate when the relay is on """

        with self.__switching_mode_lock:
            if self.is_normal_mode:
                self.relay_normal.on()
                # leave enough time for the relay to switch state. We don't want a shortcircuit
                time.sleep(constants.DELAY_RELAYS)
                self.relay_manual.on()
                self.is_normal_mode = False

    def get_image_stream(self):
        """ Takes a photo and returns a bytes object representing the image """

        with self.camera_lock:
            stream = BytesIO()
            self.camera.capture(stream, "png")
            stream.seek(0)
            return stream

        return None

    def get_video_stream(self, video_duration):
        """ Records a video and returns the byte stream """

        with self.camera_lock:
            stream = BytesIO()
            self.camera.start_recording(stream, format="h264", quality=23)
            self.camera.wait_recording(video_duration)
            self.camera.stop_recording()
            stream.seek(0)
            return stream

        return None

    def send_menu(self):
        """ Sends a message with an inline keyboard representing the menu """

        if self._menu_message:
            self._menu_message.delete()

        reply_markup = menu.generate_menu_keyboard(self)
        self._menu_message = self.send_message(menu.MESSAGE, reply_markup=reply_markup)

    def record_and_send_video(self, duration, inform=True):
        """ Records and sends a video with the specified duration. 
        If inform is True then telegram messages will be sent telling the stage of the 
        process it is i.e (recording, processing, etc)"""

        if inform:
            self.send_message(f"La grabación durará {duration} segundos")
            
        with self.get_video_stream(duration) as video_stream:
            if inform:
                self.send_message("Se ha terminado la grabación. Iniciando procesamiento")
            
            with bro_utils.convert_to_mp4(video_stream.read(), self.camera.framerate) as mp4_stream:
                self._retry_network_error(self.send_video, mp4_stream)

    def send_message(self, message, *args, **kwargs):
        """ Sends a message to the chat which is authorized to talk to """

        return self.__updater.bot.send_message(self.__authorized_chat, message, *args, **kwargs)
    
    def send_photo(self, photo, *args, **kwargs):
        """ Sends a photo (stream of bytes) to the chat which is authorized to talk to """

        return self.__updater.bot.send_photo(self.__authorized_chat, photo, *args, **kwargs)

    def send_video(self, video, *args, **kwargs):
        """ Sends a video (stream of bytes) to the chat which is authorized to talk to """

        return self.__updater.bot.send_video(self.__authorized_chat, video, *args, **kwargs)

    def add_menu_callback_query(self, callback_data, callback, end_menu=True, run_async=True):
        """ Adds a callback query triggered when a button from an inline keyboard is pressed
            and the data associated to it matches the regex. The rule I have established is
            that the menu will become a normal message after an inline button has been pressed
            so that a sort of register with the actions of the users is kept in the chat

            If 'end_menu' is True, then the menu message will be sent after the callback has
            finished"""
            
        def callback_query_wrapper(update, context):
            # there is no need to check who has typed because a callback query can only 
            # be triggered by a command
            query = update.callback_query
            query.answer()

            callback(self, update)
            if end_menu:
                self.send_menu()

        self.__dispatcher.add_handler(CallbackQueryHandler(callback_query_wrapper,
                                        pattern=f"^{callback_data}$", run_async=run_async))

    def add_button_and_command(self, name, callback, *args, **kwargs):
        """ Pressing a button is like executing a command but without typing it. This method
            avoids redundancy when adding these kinds of callbacks

            NOTE: the name of the command and the data associated to a button is the same"""

        self.add_command(name, callback, *args, **kwargs)
        self.add_menu_callback_query(name, callback, *args, **kwargs)

    def _retry_network_error(self, sending_func, stream, attempts=3, *args, **kwargs):
        """ In case of a NetworkError, retries 'attempts' times before giving up. """

        for i in range(1, attempts + 1):
            try:
                sending_func(stream, *args, **kwargs)
                break
            except NetworkError:
                # NOTE: log error in a proper manner (using logging)
                print(f"NETWORK ERROR: trying again... {i}/{attempts}")


def main():
    pin_dict = generate_pin_dict()
    bro = FourthBrother(constants.TOKEN, constants.GROUP_CHAT_ID, pin_dict,
                            camera_resolution=(288*2, 576*2), rotation=270)

    # add commands
    bro.add_button_and_command(bro_handlers.VIDEO, bro_handlers.video_command)
    bro.add_button_and_command(bro_handlers.PHOTO, bro_handlers.photo_command)
    bro.add_button_and_command(bro_handlers.ALARM, bro_handlers.alarm_command)
    bro.add_button_and_command(bro_handlers.LAMP, bro_handlers.lamp_command)

    # add menu
    bro.add_command("menu", menu.start_menu_command, end_menu=False)

    # add handlers associated to sensors
    bro.add_handler_to_device("pir_sensor", when_activated=bro_handlers.movement_handler)

    bro.start_polling(timeout=15)

    # TODO: polling at night is nonse. Establish
    # an interval of time when the bot does not poll? 

    # TODO: think about unexpected exception and the way to handle them


if __name__ == "__main__":
    main()
