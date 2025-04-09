from typing import Annotated, Any

import jwt
from fastapi import Header, HTTPException
from starlette import status


def validate_token(
    authorization: Annotated[str, Header()],
) -> dict[str, Any]:
    schema, token = authorization.split()
    if schema.lower() != 'bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized')
    try:
        parsed_token = jwt.decode(
            token,
            'wuoWElAwkrxPt0D7dSXCcK_Dmk2cVMMfPQfjbDYm9aY',
            algorithms=['HS256'],
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized')
    return parsed_token
