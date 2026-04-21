import hashlib
import hmac
import json
from urllib.parse import urlencode
from time import time


async def generateInitData(bot_token: str, user_data: dict) -> str:
    auth_date = int(time())
    init_data = {
        'auth_date': auth_date,
        'user': json.dumps(user_data, separators=(',', ':')),
    }

    data_check_string = '\n'.join(
        f"{k}={init_data[k]}" for k in sorted(init_data.keys())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256
    ).digest()

    signature = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

    init_data['hash'] = signature

    return urlencode(init_data)
