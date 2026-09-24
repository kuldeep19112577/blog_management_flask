from flask import Blueprint, request
from .connection import blog_collection
from .middleware import token_required
from datetime import datetime,timezone
from bson import ObjectId
import jwt
from dotenv import load_dotenv
import os
from pymongo import ReturnDocument



blogs_bp=Blueprint("blogs",__name__)

load_dotenv()

SECRET_KEY=os.environ["SECRET_KEY"]


@blogs_bp.post("/api/blogs")
@token_required
def handle_create_blogs(current_user_email):
    
    body=request.json
    
    if not body:
        return {"error": "Missing request body"}, 400
    
    title=body.get("title")
    content=body.get("content")
    status=body.get("status","draft")
    tags=body.get("tags",[])
    
    if not title or not content:
        return {"error": "Title and content are required fields"}, 400
    
    now=datetime.now(timezone.utc)
    
    if status == "published":
        published_at=now
    else:
        published_at=None
        
    data={
        "title":title,
        "content":content,
        "author_id":current_user_email,
        "status":status,
        "created_at":now,
        "updated_at":now,
        "published_at":published_at,
        "tags":tags,
    }
    blog_collection.insert_one(data)
    
    return {
        "message":"blog created successfully",
        "blog": {
                "title": title,
                "status": status,
                "author_id": current_user_email
        }
    }, 201

@blogs_bp.get("/api/blogs")
def handle_get_blogs():
    blogs=list(blog_collection.find({"status":"published"}))
    for i in blogs:
        i["_id"]=str(i["_id"])
        
    return blogs,200

@blogs_bp.get("/api/blogs/<id>")
def handle_get_a_blog(id):
    try:
        blog = blog_collection.find_one({"_id": ObjectId(id)})
        if not blog:
            return {"error": "Blog not found"}, 404
        blog["_id"] = str(blog["_id"])
        if blog.get("status")=="published":
            return {"blog": blog}, 200
    
        user_email = None
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                user_email = data.get("email")
                
            except jwt.ExpiredSignatureError:
                user_email = None

            except jwt.InvalidTokenError:
                user_email = None
            
        if blog.get("status") == "draft":
            if user_email and blog.get("author_id") == user_email:
                return {"blog": blog}, 200
            
        return {"error": "Blog not found"}, 404
        
        
    except Exception:
        return {"error": "Blog not found"}, 400

@blogs_bp.put("/api/blogs/<id>")
@token_required
def handle_edit_own_blogs(current_user_email,id):
    body=request.json
    
    if not body:
        return {"message":"body required"},400
    
    blog=blog_collection.find_one({"_id":ObjectId(id)})
    
    if not blog:
        return {"message":"blog not found"},400
    
    if blog.get("author_id") != current_user_email:
        return {"error": "You can only edit your own blog"}, 403

    if blog.get("status") == "published":
        return {"error": "Published blog cannot be edited"}, 403
    
    title=body.get("title", blog.get("title"))
    content=body.get("content", blog.get("content"))
        
    updated_data={
        "updated_at":datetime.now(timezone.utc),
        "title":title,
        "content":content
    }
    
    updated_blog = blog_collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": updated_data},
        return_document=ReturnDocument.AFTER
    )

    updated_blog["_id"] = str(updated_blog["_id"])
    
    return {
        "message": "Blog edited successfully",
        "blog": updated_blog
    }, 200
    

@blogs_bp.patch("/api/blogs/<id>/publish")
@token_required
def handle_publish_own_blogs(current_user_email,id):
    
    blog=blog_collection.find_one({"_id":ObjectId(id)})
    
    if not blog:
        return {"message":"blog not found"},400
        
    if blog.get("author_id") != current_user_email:
        return {"error": "You can only edit your own blog"}, 403
    
    if blog.get("status") != "draft":
        return {"error": "Only draft blogs can be published"}, 400

    updated_data={
        "status":"published",
        "published_at":datetime.now(timezone.utc)
    }
        
    updated_blog = blog_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": updated_data},
            return_document=ReturnDocument.AFTER
        )
    return {
            "message": "Blog published successfully",
            "blog": updated_blog
        }, 200

@blogs_bp.delete("/api/blogs/<id>")
@token_required
def handle_delete_own_blogs(current_user_email,id):
    pass

@blogs_bp.get("/api/me/blogs")
@token_required
def handle_Get_current_users_blogs(current_user_email):
    pass

@blogs_bp.get("/api/blogs/<id>/comments")
def handle_Get_comments(id):
    pass

@blogs_bp.post("/api/blogs/<id>/comments")
@token_required
def handle_add_comments(current_user_email,id):
    pass

@blogs_bp.post("/api/blogs/<id>/like")
@token_required
def handle_like_blog(current_user_email,id):
    pass

@blogs_bp.delete("/api/blogs/<id>/like")
@token_required
def handle_unlike_blog(current_user_email,id):
    pass