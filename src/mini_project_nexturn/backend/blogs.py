from flask import Blueprint, request
from .connection import blog_collection,blog_comments,blog_likes
from .middleware import token_required
from datetime import datetime,timezone
from bson import ObjectId
from bson.errors import InvalidId
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
    
    if status not in ["draft", "published"]:
        return {"error": "Invalid status"}, 400

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
    result = blog_collection.insert_one(data)
    
    return {
        "message":"blog created successfully",
        "blog": {
                "id":str(result.inserted_id),
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
        blog_id = ObjectId(id)
    except InvalidId:
        return {"message": "Invalid blog ID"}, 400

    blog = blog_collection.find_one({"_id": blog_id})

    if not blog:
        return {"error": "Blog not found"}, 404

    if blog.get("status") == "deleted":
        return {"error": "Blog not found"}, 404

    blog["_id"] = str(blog["_id"])

    if blog.get("status") == "published":
        return {"blog": blog}, 200

    user_email = None
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ", 1)[1]
            data = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=["HS256"]
            )
            user_email = data.get("email")

        except jwt.ExpiredSignatureError:
            user_email = None

        except jwt.InvalidTokenError:
            user_email = None

    if blog.get("status") == "draft":
        if user_email and blog.get("author_id") == user_email:
            return {"blog": blog}, 200

    return {"error": "Blog not found"}, 404

@blogs_bp.put("/api/blogs/<id>")
@token_required
def handle_edit_own_blogs(current_user_email,id):
    body=request.json
    
    if not body:
        return {"message":"body required"},400
    
    try:
        blog_id = ObjectId(id)
    except InvalidId:
        return {"message": "Invalid blog ID"}, 400
    
    blog=blog_collection.find_one({"_id":blog_id})
    
    if not blog:
        return {"message":"blog not found"},404
    
    if blog.get("author_id") != current_user_email:
        return {"error": "You can only edit your own blog"}, 403
    
    if blog.get("status") != "draft":
        return {"error": "Only draft blogs can be edited"}, 403
    
    title=body.get("title", blog.get("title"))
    content=body.get("content", blog.get("content"))
    
    if not title or not content:
        return {"error": "Title and content cannot be empty"}, 400
    
    updated_data={
        "updated_at":datetime.now(timezone.utc),
        "title":title,
        "content":content
    }
    
    updated_blog = blog_collection.find_one_and_update(
        {"_id": blog_id},
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
    try:
        blog_id = ObjectId(id)
    except InvalidId:
        return {"message": "Invalid blog ID"}, 400

    blog=blog_collection.find_one({"_id":blog_id})
    
    if not blog:
        return {"message":"blog not found"},404
        
    if blog.get("author_id") != current_user_email:
        return {"error": "You can only publish your own blog"}, 403
    
    if blog.get("status") != "draft":
        return {"error": "Only draft blogs can be published"}, 400

    updated_data={
        "status":"published",
        "published_at":datetime.now(timezone.utc)
    }
        
    updated_blog = blog_collection.find_one_and_update(
            {"_id": blog_id},
            {"$set": updated_data},
            return_document=ReturnDocument.AFTER
        )
    updated_blog["_id"] = str(updated_blog["_id"])
    return {
            "message": "Blog published successfully",
            "blog": updated_blog
        }, 200

@blogs_bp.delete("/api/blogs/<id>")
@token_required
def handle_delete_own_blogs(current_user_email,id):
    try:
        blog_id = ObjectId(id)
    except InvalidId:
        return {"message": "Invalid blog ID"}, 400
    
    blog=blog_collection.find_one({"_id":blog_id})
    if not blog:
        return {
            "message": "Blog not found"
        }, 404
        
    if blog.get("author_id")!=current_user_email:
        return{
            "message":"you're not authorized person "
        },403
    if blog.get("status") == "deleted":
        return {"message": "Blog is already deleted"}, 400 

    if blog.get("status") == "published":

        updated_blog = blog_collection.find_one_and_update(
            {"_id": blog_id},
            {
                "$set": {
                    "status": "deleted",
                    "deleted_at": datetime.now(timezone.utc)
                }
            },
            return_document=ReturnDocument.AFTER
        )
        
        updated_blog["_id"] = str(updated_blog["_id"])
        return {
            "message": "Published blog deleted successfully",
            "blog": updated_blog
        }, 200

    title=blog.get("title")
    blog_collection.find_one_and_delete({"_id":blog_id})
    
    return {"message":f"blog with {title} deleted successfully"},200
    

@blogs_bp.get("/api/me/blogs")
@token_required
def handle_Get_current_users_blogs(current_user_email):
    blogs=list(blog_collection.find({"author_id":current_user_email}))
    if not blogs:
        return {"message":f"blog with {current_user_email} not found"},404

    for blog in blogs:
        blog["_id"]=str(blog["_id"])
    
    return {
        "message":f"Blogs associated with {current_user_email}",
        "blogs":blogs
    },200

@blogs_bp.get("/api/blogs/<id>/comments")
def handle_Get_comments(id):
    try:
        blog_id = ObjectId(id)
    except InvalidId:
        return {"message": "Invalid blog ID"}, 400

    blog = blog_collection.find_one({"_id": blog_id})

    if not blog:
        return {"message": "Blog not found"}, 404
    
    comments=list(blog_comments.find({"blog_id":id}))
    
    if not comments:
        return {"message":"comments not found"},404
    for comment in comments:
        comment["_id"]=str(comment["_id"])
        
    return {
        "comments":comments
    },200

@blogs_bp.post("/api/blogs/<id>/comments")
@token_required
def handle_add_comments(current_user_email,id):
    body=request.json
    if not body:
        return {"message":"provide json body"},400
    
    comment=body.get("comment")
    if not comment:
        return {"message":"comment is required"},400
    try:
        blog_id = ObjectId(id)
    except InvalidId:
        return {"message": "Invalid blog ID"}, 400
    
    blog=blog_collection.find_one({"_id":blog_id})
    if not blog:
        return {"message": "blog not found"}, 404
    
    if blog.get("status") != "published":
        return {"message": "Comments are allowed only on published blogs"}, 403
    
    data={
        "comment":comment,
        "blog_id":id,
        "user_id":current_user_email,
        "commented_at":datetime.now(timezone.utc)
    }
    
    blog_comments.insert_one(data)

    
    return {"message":f"comment {comment} added successfully "},201

@blogs_bp.post("/api/blogs/<id>/like")
@token_required
def handle_like_blog(current_user_email,id):
    try:
        blog_id = ObjectId(id)
    except InvalidId:
        return {"message": "Invalid blog ID"}, 400
    
    blog=blog_collection.find_one({"_id":blog_id})
    if not blog:
        return {"message": "blog not found"}, 404
        
    if blog.get("status") != "published":
        return {"message": "likes are allowed only on published blogs"}, 403
    
    existing_like = blog_likes.find_one({
        "blog_id": id,
        "user_id": current_user_email
    })

    if existing_like:
        return {
            "message": "you can like only once"
        }, 400
        
    data={
        "blog_id":id,
        "user_id":current_user_email,
        "liked_at":datetime.now(timezone.utc)
    }
    blog_likes.insert_one(data)
    
    return({"message":"blog liked successfully"}),201

@blogs_bp.delete("/api/blogs/<id>/like")
@token_required
def handle_unlike_blog(current_user_email,id):
    try:
        blog_id=ObjectId(id)
    except InvalidId:
        return {"message": "Invalid blog ID"}, 400
    
    blog=blog_collection.find_one({"_id":blog_id})
    if not blog:
        return {"message": "blog not found"}, 404
    
    like=blog_likes.find_one({"blog_id":id,"user_id":current_user_email})
    if not like:
        return {"message":"like not found"},404
        
    blog_likes.find_one_and_delete({"blog_id":id,"user_id":current_user_email})
    
    return {"message":"blog unliked successfully"},200