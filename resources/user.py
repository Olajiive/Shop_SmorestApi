from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from models.user import UserModel
from db import db
from schemas import UserSchema
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from datetime import timedelta
from blocklist import BLOCKLIST


blp = Blueprint("Users", "user", description="operations on user")

@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        if UserModel.query.filter(UserModel.username==user_data["username"]).first():
            abort(409, message="This username is taken")

        user = UserModel(username = user_data["username"], password =pbkdf2_sha256.hash(user_data["password"]))

        db.session.add(user)
        db.session.commit()

        return {"message": "User Created Successfully"}, 201

@blp.route("/login")
class Login(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(UserModel.username==user_data['username']).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(identity=user.id)

            return {"access_token": access_token, "refresh_token": refresh_token}

        abort(401, message="Invalid Credentials")

@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, frsh=False, expires_delta=timedelta(days=5))
        
        return {"access_token": new_token}

@blp.route("/logout")
class Logout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        BLOCKLIST.add(jti)
        return {"message": "Sucessfully logged out "}

@blp.route("/user/<int:user_id>")
class User(MethodView):
    # Get a user by id
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    # Delete a user by id
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)

        db.session.delete(user)
        db.session.commit()

        return {"message": "User Deleted"}, 200

@blp.route("/users")
class UserList(MethodView):
    @blp.response(200,  UserSchema(many=True))
    def get(self):
        all_users = UserModel.query.all()
        return all_users


        
