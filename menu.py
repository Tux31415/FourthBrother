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

import handlers

MESSAGE = "Elige una de las siguientes opciones"

def _generate_keyboard_markup(keyboard):
    inline_keyboard = [
            [InlineKeyboardButton(btn_msg, callback_data=str(data))
                for btn_msg, data in row_buttons]
            for row_buttons in keyboard
    ]
    return InlineKeyboardMarkup(inline_keyboard)

def generate_menu_keyboard(bro):
    pir_option_msg = "Desactivar alarma" if bro.pir_activated else "Activar alarma"
    lamp_option_msg = "Encender lámpara" if bro.is_normal_mode else "Apagar lámpara"
    movement_option_msg = "Desactivar movimiento" if bro.movement_activated else "Activar movimiento"

    reply_markup = _generate_keyboard_markup([
        [(pir_option_msg, handlers.ALARM), (lamp_option_msg, handlers.LAMP)],
        [("Hacer Foto", handlers.PHOTO), (movement_option_msg, handlers.MOVEMENT)],
        [("Hacer Video", handlers.VIDEO)]
    ])

    return reply_markup

def start_menu_command(bro, update, *comm_args):
    bro.send_menu()
