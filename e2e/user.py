import pyotp


class User:
    def __init__(self, username, password, totp_seed):
        self.username = username
        self.password = password
        self.totp_seed = totp_seed
        self.totp = pyotp.TOTP(totp_seed)
