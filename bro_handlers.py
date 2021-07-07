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

import time

# measured in seconds
DEFAULT_VIDEO_DURATION = 8
MAXIMUM_VIDEO_DURATION = 30
MINIMUM_DELAY_PIR = 45


def relay_command(bro, update, *comm_args):
    if bro.is_normal_mode:
        bro.send_message("La lámpara puede ser controlado por el relé")
        bro.change_to_manual_mode()
    else:
        bro.send_message("La lámpara ya no puede ser controlada por el relé")
        bro.change_to_normal_mode()

def photo_command(bro, update, *comm_args):
    if bro.camera_lock.locked():
        bro.send_message("La cámara no se encuentra disponible en estos momentos")
        return
    
    bro.change_to_manual_mode()

    with bro.get_image_stream() as image_stream:
        bro.send_photo(image_stream)

    bro.change_to_normal_mode()

def sensor_command(bro, update, *comm_args):
    if bro.pir_activated:
        bro.send_message("El sensor pir se ha desactivado")
        bro.pir_activated = False
    else:
        bro.send_message("El sensor pir se ha activado")
        bro.pir_activated = True

def video_command(bro, update, *comm_args):
    duration = DEFAULT_VIDEO_DURATION
    if comm_args:
        try:
            duration = int(comm_args[0])
        except ValueError:
            bro.send_message("Por favor, introduce un número")
            return

    if duration > MAXIMUM_VIDEO_DURATION:
        bro.send_message(f"No puedes hacer grabaciones de más de {MAXIMUM_VIDEO_DURATION} segundos")
        return
    
    # we don't want threads to be waiting for the camera to be ready because,
    # during a period of time , we could run out of them if commands of this kind are received
    # very rapidly and it would be impossible to handle in time other commands
    if bro.camera_lock.locked():
        bro.send_message("La cámara no se encuentra disponible en estos momentos")
        return

    bro.change_to_manual_mode()
    bro.record_and_send_video(duration)
    bro.change_to_normal_mode()

def movement_handler(bro):
    if not bro.pir_activated or time.time() - bro.last_time_pir < MINIMUM_DELAY_PIR:
        return

    bro.send_message("¡¡ATENCIÓN: EL SENSOR PIR HA DETECTADO MOVIMIENTO!!")
    bro.last_time_pir = time.time()

    # if the camera is being used, wait until it is freed before sending message informing about the sitation
    # I do it in this way because, if the camera is being used, it is very likely it catches the source which
    # triggered the pir sensor
    # NOTE: the aquire() method from Lock() is the one which make the thread to sleep
    if bro.camera_lock.locked():
        bro.send_message("La cámara está siendo usada. Esperando a que termine")

    bro.change_to_manual_mode()

    bro.record_and_send_video(DEFAULT_VIDEO_DURATION)

    bro.change_to_normal_mode()
    bro.send_menu()
