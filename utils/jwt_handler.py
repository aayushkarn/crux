import datetime
from jose import JWTError, jwt

import config 


def create_access_token(subject):
    expiry_delta = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=config.ACCESS_TOKEN_EXPIRY_MINUTE)
    to_encode = {"exp":expiry_delta, "sub":str(subject)}
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, config.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject):
    expiry_delta = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=config.REFRESH_TOKEN_EXPIRY_MINUTE)
    to_encode = {"exp":expiry_delta, "sub":str(subject)}
    encoded_jwt = jwt.encode(to_encode, config.JWT_REFRESH_SECRET_KEY, config.ALGORITHM)
    return encoded_jwt

def verify_refresh_token(refresh_token):
    try:
        payload = jwt.decode(refresh_token, config.JWT_REFRESH_SECRET_KEY, algorithms=config.ALGORITHM)
        return payload["sub"]
    except JWTError:
        return None

def verify_access_token(access_token):
    try:
        # payload = jwt.decode(access_token, config.JWT_SECRET_KEY, algorithms=config.ALGORITHM,options={"verify_exp": True})
        payload = jwt.decode(access_token, config.JWT_SECRET_KEY, algorithms=config.ALGORITHM)

        print(payload)
        return payload["sub"]
    except JWTError:
        return None
    
def create_admin_access_token(subject):
    expiry_delta = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=config.ACCESS_TOKEN_EXPIRY_MINUTE)
    to_encode = {"exp":expiry_delta, "sub":str(subject)}
    encoded_jwt = jwt.encode(to_encode, config.ADMIN_JWT_SECRET_KEY, config.ALGORITHM)
    return encoded_jwt

def create_admin_refresh_token(subject):
    expiry_delta = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=config.REFRESH_TOKEN_EXPIRY_MINUTE)
    to_encode = {"exp":expiry_delta, "sub":str(subject)}
    encoded_jwt = jwt.encode(to_encode, config.ADMIN_JWT_REFRESH_SECRET_KEY, config.ALGORITHM)
    return encoded_jwt

def verify_admin_refresh_token(refresh_token):
    try:
        payload = jwt.decode(refresh_token, config.ADMIN_JWT_REFRESH_SECRET_KEY, algorithms=config.ALGORITHM)
        return payload["sub"]
    except JWTError:
        return None

def verify_admin_access_token(access_token):
    try:
        payload = jwt.decode(access_token, config.ADMIN_JWT_SECRET_KEY, algorithms=config.ALGORITHM)
        return payload["sub"]
    except JWTError:
        return None