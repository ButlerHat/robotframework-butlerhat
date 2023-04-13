import os
import ButlerRobot.keywords.vault as vault
from robot.libraries.BuiltIn import BuiltIn


credentials = {
    'user': 'gAAAAABkN81ds1Tf6Y27Ix5cb89SW-YlL-lQXJ1bOIyB12CZo7ejctLvJy6-VFGknuGDYDPSm-SvYwwoBqSuQVoLszqpOqSYfK1Jxu04vNEorDhBm-US9LU=',
    'pass': 'gAAAAABkN8SPYGibjXun4ynD1d5vCcSMXov2rPYD6jjH2IVwcMm4rqQq4drx7fHOLi_zeM0flEdeWe41bQH1uYc42JqR0U9tdg=='
}


def get_variables():
    pass_ = BuiltIn().get_variable_value('${PASSWORD}', os.environ.get('ROBOT_CICLOZERO_PASS'))
    return vault.get_credentials(pass_, credentials)
