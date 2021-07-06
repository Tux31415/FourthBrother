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

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import bro_handlers

MESSAGE = "Elige una de las siguientes opciones"

PIR_ACTIVATION, PHOTO, LAMP, MOVEMENT = range(4)

def _generate_keyboard_markup(keyboard):
    inline_keyboard = [
            [InlineKeyboardButton(btn_msg, callback_data=str(data))
                for btn_msg, data in row_buttons]
            for row_buttons in keyboard
    ]
    return InlineKeyboardMarkup(inline_keyboard)

def generate_menu_keyboard(bro):
    pir_option_msg = "Desactivar PIR" if bro.pir_activated else "Activar PIR"
    lamp_option_msg = "Encender lámpara" if bro.is_normal_mode else "Apagar lámpara"
    movement_option_msg = "Desactivar movimiento" if bro.movement_activated else "Activar movimiento"

    reply_markup = _generate_keyboard_markup([
        [(pir_option_msg, PIR_ACTIVATION), (lamp_option_msg, LAMP)],
        [("Hacer Foto", PHOTO), (movement_option_msg, MOVEMENT)],
    ])

    return reply_markup

def start_menu_command(bro, update, *comm_args):
    bro.send_menu()

# TODO: think on how to avoid redundancy in code between callback queries and commands.
# The code to be executed is very similar and in case I wanted to change part of its
# functionalites I would have to change on both sides
def photo_callback_query(bro, query, update):
    sender = update.effective_user.first_name
    query.edit_message_text(f"{sender} ha hecho una foto")

    bro_handlers.photo_command(bro, update)

def lamp_callback_query(bro, query, update):
    pass

def movement_callback_query(bro, query, update):
    pass

def pir_activation_callback_query(bro, query, update):
    sender = update.effective_user.first_name

    if bro.pir_activated:
        bro.pir_activated = False
        query.edit_message_text(f"{sender} ha desactivado el sensor PIR")
    else:
        bro.pir_activated = True
        query.edit_message_text(f"{sender} ha activado el sensor PIR")

