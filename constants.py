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
from decouple import config

TOKEN = config("TOKEN")
GROUP_CHAT_ID = config("GROUP_CHAT_ID", cast=int)

CAMERA_FRAMERATE = config("CAMERA_FRAMERATE", default=30, cast=int)
DELAY_RELAYS = config("DELAY_RELAYS", default=0.5, cast=float)
LAMP_ON_TIME = config("LAMP_ON_TIM", default=10, cast=int)

# measured in seconds
DEFAULT_VIDEO_DURATION = 8
MAXIMUM_VIDEO_DURATION = 30
MINIMUM_DELAY_PIR = 45

# reasons for quitting the program
REASON_SHUTDOWN = 1
REASON_REBOOT = 2
