import streamlit as st
import pymongo
from datetime import datetime
import pytz
import pandas as pd
import folium
from streamlit_folium import st_folium
from google_play_scraper import app

mongo_uri = st.secrets["MONGO_URI"]
client = pymongo.MongoClient(mongo_uri)
db = client["analytics"]
app_collection = db["analytics"]
location_collection = db["locations"]
ist = pytz.timezone("Asia/Kolkata")

@st.cache_data
def get_app_name_or_package(package_name):
    try:
        app_info = app(package_name, lang="en", country="in")
        return {'app_name': app_info['title'], 'app_image': app_info['icon']}
    except:
        return {'app_name': package_name, 'app_image': None}

def format_time(milliseconds):
    time = datetime.fromtimestamp(milliseconds / 1000).astimezone(ist).strftime("%d-%m-%Y %I:%M:%S.%f %p")
    return time

def get_duration(milliseconds):
    seconds = int(milliseconds / 1000)
    
    if seconds < 60:
        return f"{seconds} sec"
    
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min"
    
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h {minutes % 60}min" if minutes % 60 else f"{hours}h"
    
    days = hours // 24
    if days < 30:
        return f"{days}d {hours % 24}h" if hours % 24 else f"{days}d"
    
    months = days // 30
    if months < 12:
        return f"{months}mo {days % 30}d" if days % 30 else f"{months}mo"
    
    years = months // 12
    return f"{years}y {months % 12}mo" if months % 12 else f"{years}y"

def process_documents(docs):
    processed_data = []
    for doc in docs:
        current_time = datetime.fromtimestamp(doc['currentTimestamp'] / 1000).astimezone(ist).strftime("%d-%m-%Y %I:%M %p")
        usage_stats = sorted(
            [
                {
                    "packageName": get_app_name_or_package(stat['packageName'])['app_name'],
                    "appImage": get_app_name_or_package(stat['packageName'])['app_image'],
                    "totalTimeInForeground": stat['totalTimeInForeground'],
                    "firstTimeStamp": datetime.fromtimestamp(stat['firstTimeStamp'] / 1000).astimezone(ist).strftime("%d-%m-%Y %I:%M %p"), 
                    "lastTimeStamp": datetime.fromtimestamp(stat['lastTimeStamp'] / 1000).astimezone(ist).strftime("%d-%m-%Y %I:%M %p"),  
                }
                for stat in doc['usageStats'] if stat['totalTimeInForeground'] > 0
            ],
            key=lambda x: x['totalTimeInForeground'],
            reverse=True
        )
        if usage_stats:
            processed_data.append({
                "current_time": current_time,
                "usage_stats": usage_stats
            })
    return processed_data

def fetch_locations():
    # Fetch location data from the MongoDB collection
    return list(location_collection.find().sort("time", -1))

def display_map(latitude, longitude):
    # Create a map centered around the given latitude and longitude
    location_map = folium.Map(location=[latitude, longitude], zoom_start=15)
    folium.Marker([latitude, longitude]).add_to(location_map)
    # Display the map using Streamlit's folium component
    return st_folium(location_map, width=725)

# Streamlit layout for main navigation
page = st.sidebar.radio("Select a Page", ["Location Page", "App Usage Stats",])

if page == "App Usage Stats":
    # Fetch and process app usage data
    docs = list(app_collection.find().sort("currentTimestamp", -1))
    data = process_documents(docs)

    # Sidebar for selecting a document
    st.sidebar.title("Timestamps")
    selected_time = st.sidebar.radio("Select a document", [doc["current_time"] for doc in data])
    
    for doc in data:
        if doc["current_time"] == selected_time:
            st.write(f"### Usage Stats for {selected_time}")
            df = pd.DataFrame(doc["usage_stats"])
            for i, row in df.iterrows():
                col1, col2 = st.columns([1, 4])
                if row['appImage']:
                    col1.image(row['appImage'], width=50)
                col2.write(f"**{row['packageName']}**")
                col2.write(f"Duration: {get_duration(row['totalTimeInForeground'])}")
                col2.write(f"First Used: {row['firstTimeStamp']}")
                col2.write(f"Last Used: {row['lastTimeStamp']}")
                st.write("---")
            st.write("#### Total Time in Foreground (minutes) per App")
            chart_data = df.set_index("packageName")["totalTimeInForeground"]
            st.bar_chart(chart_data)
            break

elif page == "Location Page":
    # Fetch location data
    locations = fetch_locations()

    # Sidebar for selecting a location
    st.sidebar.title("Location Timestamps")
    selected_time = st.sidebar.radio(
        "Select a time",
        [format_time(location["time"]) for location in locations]
    )

    for location in locations:
        if format_time(location["time"]) == selected_time:
            st.write(f"### Location Stats for {selected_time}")
            
            # Get latitude, longitude and formatted time
            latitude = location["latitude"]
            longitude = location["longitude"]
            formatted_time = format_time(location["time"])

            # Display the location details
            st.write(f"**Latitude:** {latitude}")
            st.write(f"**Longitude:** {longitude}")
            st.write(f"**Timestamp (IST):** {formatted_time}")
            
            # When the time is clicked, display the map
            # if st.button("Show Location on Map"):
            display_map(latitude, longitude)
            # break
