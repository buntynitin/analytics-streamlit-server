import streamlit as st
import pymongo
from datetime import datetime
from google_play_scraper import app
import pandas as pd
import pytz

mongo_uri = st.secrets["MONGO_URI"]
client = pymongo.MongoClient(mongo_uri)
db = client["analytics"]
collection = db["analytics"]
ist = pytz.timezone("Asia/Kolkata")

@st.cache_data
def get_app_name_or_package(package_name):
    try:
        app_info = app(package_name, lang="en", country="in")
        return {'app_name': app_info['title'], 'app_image': app_info['icon']}
    except:
        return {'app_name': package_name, 'app_image': None}

def format_time(milliseconds):
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

# Fetch and process data
docs = list(collection.find().sort("currentTimestamp", -1))
data = process_documents(docs)

# Streamlit layout
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
            col2.write(f"Duration: {format_time(row['totalTimeInForeground'])}")
            col2.write(f"First Used: {row['firstTimeStamp']}")
            col2.write(f"Last Used: {row['lastTimeStamp']}")
            st.write("---")
        st.write("#### Total Time in Foreground (minutes) per App")
        chart_data = df.set_index("packageName")["totalTimeInForeground"]
        st.bar_chart(chart_data)
        break
