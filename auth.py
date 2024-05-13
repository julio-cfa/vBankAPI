from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Header, HTTPException

SECRET = "bank1100500934930"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 1000

def createAccessToken(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    payload = {"bearer_token": encoded_jwt}
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
        print(f"Error: {jwt_error}")
        return False



