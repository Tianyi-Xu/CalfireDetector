from rest_api.models.user import UserModel
import hmac  # safer way to compare string with different python version and encoding systems

def authenticate(username, password):
    user = UserModel.find_by_username(username)
    if user and hmac.compare_digest(user.password, password):
        return user

# unique to flask-jwt
def identity(payload):
    user_id = payload['identity']
    return UserModel.find_by_id(user_id)
