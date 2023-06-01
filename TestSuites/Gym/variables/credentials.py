import os
import ButlerRobot.keywords.vault as vault
from robot.libraries.BuiltIn import BuiltIn


credentials = {
    'gym_pass': 'gAAAAABkcMddqmpRk0CpOg1D0yJKDf_zpIkaM0EEvslJsOMSpJ6TPh4TG0nZTzQB-TUoNotWRTTF0tGAIbgVMzvcZKS3Ohbp1g==',
}


def get_variables():
    pass_ = BuiltIn().get_variable_value('${ROBOT_GYM_PASS}', os.environ.get('ROBOT_GYM_PASS'))
    assert pass_, 'Password not found. Define ROBOT_CICLOZERO_PASS environment variable or set it as variable.'
    return vault.get_credentials(pass_, credentials)
