from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Header, HTTPException

SECRET = "bank1100500934930"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 500000

def createAccessToken(data: dict, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, SECRET, algorithm=ALGORITHM)
    payload = {"type":"bearer", "token": encoded_jwt}
    return payload

def validateAccessToken(authorization: Optional[str] = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        token_type, token_value = authorization.split()
    except:
        raise HTTPException(status_code=401, detail="Token not in the right format. Use 'Authorization: Bearer <token>'")
    
    if token_type != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid Token Type")

    try:
        payload = jwt.decode(token_value, SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError as jwt_error:
        if jwt_error:
            raise HTTPException(status_code=500, detail=f"{jwt_error}")
        else:
            raise HTTPException(status_code=400, detail="Unauthorized")



