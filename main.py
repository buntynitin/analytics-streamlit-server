import streamlit as st
import pymongo
from datetime import datetime
import pandas as pd
import os

MONGO_URI = os.environ.get("MONGO_URI")
client = pymongo.MongoClient("MONGO_URI")
db = client["analytics"]
collection = db["analytics"]

# Function to process MongoDB documents
def process_documents(docs):
    processed_data = []
    for doc in docs:
        current_time = datetime.fromtimestamp(doc['currentTimestamp'] / 1000).strftime("%d-%m-%Y %I:%M %p")
        usage_stats = [
            {
                "packageName": stat['packageName'],
                "totalTimeInForeground": stat['totalTimeInForeground'] / 60000,  # Convert to minutes
                "lastTimeStamp": datetime.fromtimestamp(stat['lastTimeStamp'] / 1000).strftime("%I:%M %p")
            }
            for stat in doc['usageStats'] if stat['totalTimeInForeground'] > 0
        ]
        
        # Only add documents with relevant usage stats
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
        st.write(df[['packageName', 'totalTimeInForeground', 'lastTimeStamp']])
        st.write("#### Total Time in Foreground (minutes) per App")
        chart_data = df.set_index("packageName")["totalTimeInForeground"]
        st.bar_chart(chart_data)
        break
