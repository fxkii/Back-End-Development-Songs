from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

#health route
@app.route("/health")
def health():
    return jsonify(dict(status="OK")),200

#count route
@app.route("/count")
def count():
    if songs_list:
        return jsonify(count=len(songs_list)), 200
    return {"message":"Internal Server Error"}, 500

#get song
@app.route("/song", methods=['GET'])
def songs():
    data = db.songs.find()
    #data_list = [song for song in data]
    
    if data:
        return parse_json(data), 200
    return {},500

@app.route("/song/<int:id>", methods=["GET"])
def get_songs_by_id(id):
    data = db.songs.find_one({"id": id})
    if data:
        return parse_json(data),200
    else:
        return {"message":f"song with id {id} not found"}, 404

@app.route("/song", methods=["POST"])
def create_song():
    rec = request.json
    data = db.songs.find()
    data_list = [song for song in data]
    for check in data_list:
        if check["id"] == rec["id"]:
            return {"Message":f"song with id {check['id']} already present"}, 302
    
    insert_id: InsertOneResult = db.songs.insert_one(rec)
    return {"inserted id": parse_json(insert_id.inserted_id)}, 201
    