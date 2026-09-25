from flask import Blueprint, request
from .connection import users_collection
from werkzeug.security import generate_password_hash,check_password_hash
import jwt
from datetime import timedelta,datetime,timezone
import os
from dotenv import load_dotenv


auth_bp = Blueprint("auth", __name__)

load_dotenv()

SECRET_KEY=os.environ["SECRET_KEY"]


@auth_bp.post("/api/auth/register")
def handle_register():
    body=request.json
    
    if not body:
        return {"error": "Missing request body"}, 400
    
    name=body.get("name")
    email = body.get("email")
    password=body.get("password")
    
    if not name or not email or not password:
        return {"error": "Name, email, and password are required"}, 400
    email=email.strip().lower()
    if users_collection.find_one({"email": email}):
        return {"error": "A user with this email already exists"}, 400
    
    hashed_password=generate_password_hash(password)
    
    data={
        "name":name,
        "email":email,
        "password":hashed_password
    }
    
    
    users_collection.insert_one(data)
    
    return {
        "message":f"user {name} registered successfully"
            }, 201

@auth_bp.post("/api/auth/login")
def handle_login():
    body=request.json
    
    if not body:
        return {"error": "Missing request body"}, 400

    email=body.get("email")
    password=body.get("password")
    
    if not email or not password:
        return {"error": "email and password are required"}, 400
    
    email=email.strip().lower()
    user=users_collection.find_one({"email":email})
    
    if not user or not check_password_hash(user["password"],password):
        return {"error": "Invalid email or password"}, 401
    
    payload={
        "email":user["email"],
        "exp":datetime.now(timezone.utc)+timedelta(hours=1)
    }
    
    token=jwt.encode(payload,SECRET_KEY,algorithm="HS256")
    
    
    return {
        "message": f"Welcome back, {user['name']}!",
        "token":token
    
    }, 200

