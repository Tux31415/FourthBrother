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

from gpiozero import DigitalOutputDevice

class NegativeLogicRelay(DigitalOutputDevice):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, initial_value=True,  **kwargs)
    
    @property
    def value(self):
        return not super().value

    @value.setter
    def value(self, value):
        super().value = not value

    def on(self):
        super().off()

    def off(self):
        super().on()
