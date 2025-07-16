import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from shared.core.settings import settings

IV_LENGTH = 12
AUTH_TAG_LENGTH = 16
KEY_LENGTH = 32


def decrypt_token(encrypted_token: str) -> str:
    try:
        key = get_encryption_key()

        iv_b64, auth_tag_b64, ciphertext_b64 = encrypted_token.split(":")

        iv = base64.b64decode(iv_b64)
        auth_tag = base64.b64decode(auth_tag_b64)
        ciphertext = base64.b64decode(ciphertext_b64)

        if len(iv) != IV_LENGTH or len(auth_tag) != AUTH_TAG_LENGTH:
            raise ValueError("Invalid IV or authentication tag length.")

        aesgcm = AESGCM(key)

        decrypted_token_bytes = aesgcm.decrypt(iv, ciphertext + auth_tag, None)

        return decrypted_token_bytes.decode("utf-8")

    except (ValueError, TypeError) as e:
        print(f"Decryption failed due to invalid format or key: {e}")
        raise ValueError("Decryption failed: Invalid token format or key configuration.")
    except Exception as e:
        print(f"Decryption failed with an unexpected error: {e}")
        raise ValueError("Decryption failed: Token is invalid or has been tampered with.")


def get_encryption_key() -> bytes:
    token_encryption_key_b64 = settings.TOKEN_ENCRYPTION_KEY
    if not token_encryption_key_b64:
        raise ValueError("TOKEN_ENCRYPTION_KEY environment variable not set.")

    key = base64.b64decode(token_encryption_key_b64)
    if len(key) != KEY_LENGTH:
        raise ValueError(f"Invalid TOKEN_ENCRYPTION_KEY length. Must be {KEY_LENGTH} bytes.")

    return key
