'''

Copyright 2018 Alexander Shuping

This file is part of Pysocial.

Pysocial is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Pysocial is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Pysocial.  If not, see <http://www.gnu.org/licenses/>.

'''

from social import configurer, database_io
from social_renderer import renderer
from social_ui import basic_console_ui

config = configurer()
db_io = database_io(config)
rend = renderer(db_io, config)
u = basic_console_ui(config, db_io, rend)
if u.begin() == 0:
	u.loop()
else:
	u.log_severe('Fatal error!')
