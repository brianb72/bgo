from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restful import Resource, Api
from werkzeug.routing import BaseConverter
from database import DBAccess, DBAccessLookupNotFound, DBAccessGameRecordError, DBAccessException, DBAccessDuplicate

# From https://exploreflask.com/en/latest/views.html
class ListConverter(BaseConverter):
    def to_python(self, value):
        return value.split('+')

    def to_url(selfself, values):
        return '+'.join(BaseConverter.to_url(value) for value in values)

app = Flask(__name__)
api = Api(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.url_map.converters['list'] = ListConverter
db = DBAccess('database.sqlite')

class NextMoveData(Resource):
    def get(self, move_list):
        try:
            print(f'Got {len(move_list)} moves [{move_list}]')
            next_move_dict = db.get_next_move_counter_for_moves(move_list)
        except DBAccessException as e:
            message = f'Error while accessing database! {e}'
            print(message)
            data = {'message': message}
            return jsonify(data)
        except DBAccessLookupNotFound:
            message = f'No data found'
            data = {'message': message}
            return jsonify(data)

        # data = { next_move_dict }
        data = [{'move': k, 'count': v} for k,v in next_move_dict.items()]
        return jsonify(data)

class Home(Resource):
    def get(self):
        return jsonify({'message': 'hello world'})

    def post(self):
        data = request.get_json()
        return jsonify({'data': data}), 201

api.add_resource(Home, '/api')
api.add_resource(NextMoveData, '/api/nextmove/<list:move_list>')


if __name__ == '__main__':
    app.run(debug = True)
