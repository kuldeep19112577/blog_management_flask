from flask import Flask
from .auth import auth_bp
from .blogs import blogs_bp

app=Flask(__name__)

app.register_blueprint(auth_bp)
app.register_blueprint(blogs_bp)

if __name__=="__main__":
    app.run(debug=True,use_reloader=False)