from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_googlemaps import GoogleMaps, Map
from flask_pymongo import PyMongo
from pymongo import MongoClient
from yelpapi import YelpAPI
import os
import requests

# This is for the kickstar
from bson.objectid import ObjectId
import jinja2
from pprint import PrettyPrinter
from random import randint

load_dotenv()
mongodb_username = os.getenv('mongodb_username')
mongodb_password = os.getenv('mongodb_password')
mongodb_name = 'kickstarter'
yelp_api = YelpAPI(os.getenv('yelp_api_key'), timeout_s = 3.0)
google_maps_api_key = os.getenv('google_maps_api_key')

app = Flask(__name__)
app.secret_key = os.urandom(24)
GoogleMaps(app, key=google_maps_api_key)

client = MongoClient(f"mongodb+srv://{mongodb_username}:{mongodb_password}@cluster0.uzxh5.mongodb.net/{mongodb_name}?retryWrites=true&w=majority")
db = client[mongodb_name]

def get_coordinates(API_KEY, address_text):
    ''' google maps api to get coordinates from address '''
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json?address="
        + address_text
        + "&key="
        + API_KEY
    ).json()
    return response["results"][0]["geometry"]["location"]

@app.route('/')
def homepage():
    return "Hello, world!"



''' The code for the kickstarter routes + database is below '''
@app.route('/kickstarter')
def kick_list():
    """Displays the list of startups"""

    startup_data = db.startups.find({})

    context = {
        'startups' : startup_data
    }
    return render_template('startup_list.html', **context)

@app.route('/search_store', methods=['GET', 'POST'])
def search_store():
    ''' Search for local stores '''
    coordinates_list = []

    if request.method == 'POST':
        location = ''
        #checks if ip address is being forwarded. depends if running locally or deployed
        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            response = requests.get("http://ip-api.com/json")
            js = response.json()

            city = js['city']
            lat = js['lat']
            lng = js['lon']

        else:
            ip = request.environ['HTTP_X_FORWARDED_FOR']
            response = requests.get(f"http://ip-api.com/json/{ip}")
            js = response.json()

            city = js['city']
            lat = js['lat']
            lng = js['lon']
    
        store_name = request.form.get('store_name')
        search_results = yelp_api.search_query(term = store_name, latitude = lat, longitude = lng, categories = "vegan")
        business_info = search_results['businesses']
        
        for coordinate in business_info:
            coordinates_dict = {}
            coordinates_dict['icon'] = "/static/images/leaf_pin.png"
            coordinates_dict['lat'] = coordinate['coordinates']['latitude']
            coordinates_dict['lng'] = coordinate['coordinates']['longitude']

            coordinates_list.append(coordinates_dict)
        print(coordinates_list)

        business_map = Map(
            identifier = "test-map",
            style = "height:700px;width:700px;margin:0;",
            lat = lat,
            lng = lng,
            markers = coordinates_list
        )

        return render_template('display_store.html', business_info = business_info, business_map = business_map)

    else:
        return render_template('search_store.html')



if __name__ == '__main__':
    app.run(debug=True)
