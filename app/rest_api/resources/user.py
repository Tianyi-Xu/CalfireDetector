from flask_restful import Resource, reqparse
from rest_api.models.user import UserModel


class UserRegister(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
    type=str,
    required=True,
    help='This username field cannot be blank.'
    )

    parser.add_argument('password',
    type=str,
    required=True,
    help='This password field cannot be blank.'
    )

    parser.add_argument('address',
    type=str,
    required=True,
    help='This address field cannot be blank.'
    )
    parser.add_argument('email',
    type=str,
    required=True,
    help='This email field cannot be blank.'
    )


    def post(self):
        data = UserRegister.parser.parse_args()
        print(data)
        if UserModel.find_by_username(data['username']):
            return {'message': 'User with that username has already exist'}, 400

        user = UserModel(**data)
        user.save_to_db()
        return {'message':'user was registered successfully'}, 201


