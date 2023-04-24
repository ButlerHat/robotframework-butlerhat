import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


def encrypt(password: str, txt_to_encrypt: str) -> str:
    """
    Encripta el texto 'txt_to_encrypt' utilizando la clave 'password' y devuelve el resultado como una cadena de texto.

    Args:
        password (str): La clave para encriptar el texto.
        txt_to_encrypt (str): El texto que se desea encriptar.

    Returns:
        str: El texto encriptado.
    """
    pass_ = password.encode()
    salt = b'salt_'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(pass_))
    cipher_suite = Fernet(key)
    cipher_text = cipher_suite.encrypt(txt_to_encrypt.encode())
    return cipher_text.decode()


def decrypt(password: str, txt_to_decrypt: str) -> str:
    """
    Desencripta el texto 'txt_to_decrypt' utilizando la clave 'password' y devuelve el resultado como una cadena de texto.

    Args:
        password (str): La clave para desencriptar el texto.
        txt_to_decrypt (str): El texto que se desea desencriptar.

    Returns:
        str: El texto desencriptado.
    """
    pass_ = password.encode()
    salt = b'salt_'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(pass_))
    cipher_suite = Fernet(key)
    plain_text = cipher_suite.decrypt(txt_to_decrypt.encode())
    return plain_text.decode()


def get_credentials(password: str, credentials: dict):
    for key, value in credentials.items():
        credentials[key] = decrypt(password, value)
    return credentials


if __name__ == '__main__':
    import os
    password = os.getenv('ROBOT_CICLOZERO_PASS')
    assert password, 'Password not found. Define ROBOT_CICLOZERO_PASS environment variable or set it as variable.'
    print('password: ' + password)