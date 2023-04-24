import os
import ButlerRobot.keywords.vault as vault
from robot.libraries.BuiltIn import BuiltIn


credentials = {
    'odoo_user': 'gAAAAABkQQ-cL1kJByvvnZcFSAnNcl8zTI5dP3pZu-3-1kwTT4hjpRVcvuMXMtAoZ_bqPtkqAtNmo6ihzer4i-KTt4LS4nXyrpk0L9TKMduJca1gpDkcLvE=',
    'odoo_pass': 'gAAAAABkQRC2VBOMGiYmqWoA4iYQaKfJuTTdlggEoYyyvOWKX-x0i3w81or8PKY4e-XnFVPHUftmbK34HgOsCmM1zX_vHF5jsQ==',
    'amazon_user': 'gAAAAABkQRRpB-F3IN9FAcrTxlAAEuMcnQiF0JRx8qZBHXyxw-pIUDl26BrMehMCKtiqOs12utj7O6hvQpqiUJiiVWEPwihFzA==',
    'amazon_pass': 'gAAAAABkQQ-cS29l1B7fmtReo2nKvWk5ExYYBgIPEX43bhOJIDSrmHJQQJH-15L4IY97GyrA3k0anX2TDaTrmxfFGk0Uln_DMQ==',
    'otp_amazon': 'gAAAAABkQQ-cUSZNeaOUCgfqrBtvu3Nn-3zwG7OZZHFikFasw1ibGRvIoNBRgekXSZDJz8JjNflPObMAYbWL9qCf3jcy2MmTocoZUZ8TnlweW6M6fKpAf41SXu4ip21ds0aBlld6-UaYs52HJxQdUcO0yydI8iGCrg=='
}


def get_variables():
    pass_ = BuiltIn().get_variable_value('${ROBOT_CICLOZERO_PASS}', os.environ.get('ROBOT_CICLOZERO_PASS'))
    assert pass_, 'Password not found. Define ROBOT_CICLOZERO_PASS environment variable or set it as variable.'
    return vault.get_credentials(pass_, credentials)
