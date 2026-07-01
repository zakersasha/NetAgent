import bcrypt as bcrypt_lib


def hash_password(password: str) -> str:
    return bcrypt_lib.hashpw(password.encode("utf-8"), bcrypt_lib.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt_lib.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
