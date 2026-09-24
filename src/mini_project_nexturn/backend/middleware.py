from functools import wraps
from flask import request
import jwt
import os

SECRET_KEY = os.environ["SECRET_KEY"]

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return {"error": "Token is missing! Please login first."}, 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_email = data["email"]
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired! Please login again."}, 401
        except jwt.InvalidTokenError:
            return {"error": "Invalid token! Authentication failed."}, 401

        return f(current_user_email, *args, **kwargs)

    return decorated
