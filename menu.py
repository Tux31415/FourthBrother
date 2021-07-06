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

MAIN_MENU, PIR_ACTIVATION, PHOTO = range(3)

def _generate_keyboard_markup(keyboard):
    inline_keyboard = [
            [InlineKeyboardButton(btn_msg, callback_data=str(data))
                for btn_msg, data in row_buttons]
            for row_buttons in keyboard
    ]
    return InlineKeyboardMarkup(inline_keyboard)

def generate_menu_keyboard(bro):
    pir_option_msg = "Desactivar PIR" if bro.pir_activated else "Activar PIR"

    reply_markup = _generate_keyboard_markup([
        [(pir_option_msg, PIR_ACTIVATION)],
        [("Hacer Foto", PHOTO)]
    ])

    return reply_markup

def start_menu_command(bro, update, *comm_args):
    bro.send_menu()

def photo_callback_query(bro, query, update):
    sender = update.effective_user.first_name
    query.edit_message_text(f"{sender} ha hecho una foto")

    bro_handlers.photo_command(bro, update)

def pir_activation_callback_query(bro, query, update):
    sender = update.effective_user.first_name

    if bro.pir_activated:
        bro.pir_activated = False
        query.edit_message_text(f"{sender} ha desactivado el sensor PIR")
    else:
        bro.pir_activated = True
        query.edit_message_text("{sender} ha activado el sensor PIR")

