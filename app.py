from flask import Flask, jsonify, render_template
from backend.config import LocalDevelopmentConfig
from backend.database import db  # Import from database.py
from backend.models import Admin, Student, Company, PlacementDrive, Application
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from datetime import datetime
from backend.routes import auth_bp

jwt = JWTManager()

def createApp():
    # Change "../frontend" to just "frontend"
    app = Flask(__name__, template_folder="frontend", static_folder="frontend")
    app.config.from_object(LocalDevelopmentConfig)
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_vue(path):
        return render_template("index.html")
    
    return app 

app = createApp()

with app.app_context(): 
    #db.drop_all()
    db.create_all()

    admin = Admin.query.first()
    if not admin: 
        password_hash = generate_password_hash('admin123')
        admin = Admin(email='admin@gmail.com', name='admin', password_hash=password_hash)
        db.session.add(admin)
        db.session.commit()



@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'message': 'Access granted!', 'user': current_user})


if __name__ == "__main__":
    app.run(debug=True)