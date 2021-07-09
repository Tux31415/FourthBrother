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

import os

import time
import constants

PHOTO = "foto"
LAMP = "lamp"
MOVEMENT = "movimiento"
VIDEO = "video"
ALARM = "alarma"
REBOOT = "reiniciar"

def lamp_command(bro, update, *com_args):
    sender = update.effective_user.first_name

    if bro.is_normal_mode:
        bro.send_message(f"{sender} ha encendido la lámpara")
        bro.change_to_manual_mode()
    else:
        bro.send_message(f"{sender} ha apagado la lámpara")
        bro.change_to_normal_mode()

def photo_command(bro, update, *comm_args):
    sender = update.effective_user.first_name
    bro.send_message(f"{sender} ha hecho una foto")

    if bro.camera_lock.locked():
        bro.send_message("La cámara no se encuentra disponible en estos momentos")
        return
    
    bro.change_to_manual_mode()

    with bro.get_image_stream() as image_stream:
        bro.send_photo(image_stream)

    bro.change_to_normal_mode()

def alarm_command(bro, update, *comm_args):
    sender = update.effective_user.first_name

    if bro.pir_activated:
        bro.send_message(f"{sender} ha desactivado la alarma")
        bro.pir_activated = False
    else:
        bro.send_message(f"{sender} ha activado la alarma")
        bro.pir_activated = True

def video_command(bro, update, *comm_args):
    sender = update.effective_user.first_name

    bro.send_message(f"{sender} ha iniciado una grabación")

    duration = constants.DEFAULT_VIDEO_DURATION
    if comm_args:
        try:
            duration = int(comm_args[0])
        except ValueError:
            bro.send_message("Por favor, introduce un número")
            return

    if duration > constants.MAXIMUM_VIDEO_DURATION:
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

# in order for this to work, the bot has to be executed as a root user
def reboot_command(bro, update, *comm_args):
    sender = update.effective_user.first_name

    # the uid of the administrator is almost always 0.
    # TODO: find a more portable way to check it in case a OS for the raspberry does
    # not follow that convention

    if os.getuid() != 0:
        bro.send_message(f"{sender} ha intentado reiniciar el bot pero este último no dispone"
                            " de permisos de superusuario")
        return


    bro.send_message(f"{sender} ha reiniciado el bot. Los comandos que se manden serán"
                        "ignorados hasta que el bot esté listo de nuevo")

    self.reason_for_exiting = constants.REASON_REBOOT
    self.exiting_event.set()

def movement_command(bro, update, *comm_args):
    pass

def movement_handler(bro):
    if not bro.pir_activated or time.time() - bro.last_time_pir < constants.MINIMUM_DELAY_PIR:
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

    bro.record_and_send_video(constants.DEFAULT_VIDEO_DURATION)

    bro.change_to_normal_mode()
    bro.send_menu()
