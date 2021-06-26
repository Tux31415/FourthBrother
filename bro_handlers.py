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

import subprocess
import time

# measured in seconds
DEFAULT_VIDEO_DURATION = 5 
MAXIMUM_VIDEO_DURATION = 30
MINIMUM_DELAY_PIR = 15


def relay_command(bro, update, context):
    if bro.relay.value:
        bro.send_message("El relé se ha apagado")
        bro.relay.off()
    else:
        bro.send_message("El relé se ha encendido")
        bro.relay.on()
        
def photo_command(bro, update, context):
    if bro.using_camera.is_set():
        bro.send_message("La cámara no se encuentra disponible")
        return

    bro.using_camera.set()

    with bro.get_image_stream() as image_stream:
        bro.send_photo(image_stream)

    bro.using_camera.clear()

# TODO: add inline keyboards to choose this
def sensor_command(bro, update, context):
    if bro.pir_activated:
        bro.send_message("El sensor pir se ha desactivado")
        bro.pir_activated = False
    else:
        bro.send_message("El sensor pir se ha activado")
        bro.pir_activated = True

def video_command(bro, update, context):
    if bro.using_camera.is_set():
        bro.send_message("La cámara no se encuentra disponible")
        return
    
    bro.using_camera.set()

    duration = DEFAULT_VIDEO_DURATION
    if context.args:
        try:
            duration = int(context.args[0])
        except ValueError:
            bro.send_message("Por favor, introduce un número")
            bro.using_camera.clear()
            return

    if duration > MAXIMUM_VIDEO_DURATION:
        bro.send_message(f"No puedes hacer grabaciones de más de {MAXIMUM_VIDEO_DURATION} segundos")
        bro.using_camera.clear()
        return
    
    bro.record_and_send_video(duration)
    bro.using_camera.clear()

def movement_handler(bro):
    if not bro.pir_activated or time.time() - bro.last_time_pir < MINIMUM_DELAY_PIR:
        return

    bro.send_message("¡¡ATENCIÓN: EL SENSOR PIR HA DETECTADO MOVIMIENTO!!")
    bro.last_time_pir = time.time()

    # TODO: this is an emergency situation. If, for some reason, we were using the recording, stop it
    bro.using_camera.set()
    bro.record_and_send_video(MAXIMUM_VIDEO_DURATION)
    bro.using_camera.clear()
