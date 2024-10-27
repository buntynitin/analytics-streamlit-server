import streamlit as st
import pymongo
from datetime import datetime
import pandas as pd
import pytz

mongo_uri = st.secrets["MONGO_URI"]
client = pymongo.MongoClient(mongo_uri)
db = client["analytics"]
collection = db["analytics"]
ist = pytz.timezone("Asia/Kolkata")

def process_documents(docs):
    processed_data = []
    for doc in docs:
        current_time = datetime.fromtimestamp(doc['currentTimestamp'] / 1000).astimezone(ist).strftime("%d-%m-%Y %I:%M %p")
        usage_stats = sorted(
            [
                {
                    "packageName": stat['packageName'],
                    "totalTimeInForeground": stat['totalTimeInForeground'] / 60000,
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
docs = list(collection.find())
data = process_documents(docs)

# Streamlit layout
st.sidebar.title("Timestamps")
selected_time = st.sidebar.radio("Select a document", [doc["current_time"] for doc in data])
for doc in data:
    if doc["current_time"] == selected_time:
        st.write(f"### Usage Stats for {selected_time}")
        df = pd.DataFrame(doc["usage_stats"])
        st.write(df[['packageName', 'totalTimeInForeground', 'firstTimeStamp', 'lastTimeStamp']])
        st.write("#### Total Time in Foreground (minutes) per App")
        chart_data = df.set_index("packageName")["totalTimeInForeground"]
        st.bar_chart(chart_data)
        break
