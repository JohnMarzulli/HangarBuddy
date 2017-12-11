""" Main entry code for PiWarmer """
# !python
#
#
# Author: Mari DeGrazia
# http://az4n6.blogspot.com/
# arizona4n6@gmail.com
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You can view the GNU General Public License at <http://www.gnu.org/licenses/>
#
# Written for Python 2.7
# You will need to "pip install pyserial"
#
# Includes a GPIO mock for development\testing under Windows

import logging
import logging.handlers
import PiWarmerConfiguration
from lib.logger import Logger
import command_processor


CONFIGURATION = PiWarmerConfiguration.PiWarmerConfiguration()

LOG_LEVEL = logging.INFO

LOGGER = logging.getLogger("heater")
LOGGER.setLevel(LOG_LEVEL)
HANDLER = logging.handlers.RotatingFileHandler(
    CONFIGURATION.log_filename, maxBytes=1048576, backupCount=3)
HANDLER.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)-8s %(message)s'))
LOGGER.addHandler(HANDLER)

if __name__ == '__main__':
    COMMAND_PROCESSOR = command_processor.CommandProcessor(CONFIGURATION, Logger(LOGGER))
    COMMAND_PROCESSOR.run_pi_warmer()
