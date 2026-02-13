import streamlit as st
import pymongo
from datetime import datetime
import pytz
import pandas as pd
import folium
from streamlit_folium import st_folium
from google_play_scraper import app
import math
import html as html_module

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Device Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ─────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Sidebar ────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #f8f9fb;
    border-right: 1px solid #e8e8ef;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #333 !important;
    font-weight: 500;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    color: #6c63ff !important;
}

/* ── Cards ──────────────────────────────────────── */
.card {
    background: #ffffff;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #f0f0f5;
    transition: transform 0.15s, box-shadow 0.15s;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.10);
}

/* ── Notification card ──────────────────────────── */
.notif-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.7rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    border-left: 4px solid #6c63ff;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}
.notif-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.10);
}
.notif-icon {
    font-size: 2rem;
    min-width: 42px;
    text-align: center;
}
.notif-body {
    flex: 1;
}
.notif-title {
    font-weight: 600;
    font-size: 1rem;
    color: #1a1a2e;
    margin-bottom: 2px;
}
.notif-text {
    color: #555;
    font-size: 0.92rem;
    margin-bottom: 4px;
}
.notif-meta {
    color: #999;
    font-size: 0.78rem;
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}
.notif-meta span {
    display: inline-flex;
    align-items: center;
    gap: 3px;
}

/* ── App usage row ──────────────────────────────── */
.app-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.8rem 1rem;
    background: #ffffff;
    border-radius: 12px;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    border: 1px solid #f0f0f5;
}
.app-row:hover {
    background: #fafaff;
}
.app-icon img {
    border-radius: 12px;
    width: 48px;
    height: 48px;
    object-fit: cover;
}
.app-info {
    flex: 1;
}
.app-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: #1a1a2e;
}
.app-detail {
    font-size: 0.82rem;
    color: #777;
    margin-top: 2px;
}
.app-duration {
    font-weight: 700;
    font-size: 1rem;
    color: #6c63ff;
    min-width: 70px;
    text-align: right;
}

/* ── Metric cards ───────────────────────────────── */
.metric-card {
    background: linear-gradient(135deg, #6c63ff 0%, #4834d4 100%);
    border-radius: 14px;
    padding: 1.2rem;
    color: white;
    text-align: center;
}
.metric-card.green {
    background: linear-gradient(135deg, #00b894 0%, #00a186 100%);
}
.metric-card.orange {
    background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
}
.metric-card.blue {
    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
}
.metric-label {
    font-size: 0.82rem;
    opacity: 0.85;
    margin-top: 4px;
}

/* ── Page title ─────────────────────────────────── */
.page-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1a1a2e;
    margin-bottom: 0.3rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.page-subtitle {
    color: #888;
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
}

/* ── Pagination ─────────────────────────────────── */
.pagination-info {
    text-align: center;
    color: #999;
    font-size: 0.82rem;
    margin-top: 0.3rem;
}

/* ── Location card ──────────────────────────────── */
.loc-stat {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0;
}
.loc-stat-icon {
    font-size: 1.2rem;
}
.loc-stat-label {
    color: #888;
    font-size: 0.82rem;
}
.loc-stat-value {
    font-weight: 600;
    font-size: 0.95rem;
    color: #1a1a2e;
}

/* Hide default streamlit components for cleaner look */
div[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── MongoDB Connection ───────────────────────────────────────────────────────
mongo_uri = st.secrets["MONGO_URI"]
client = pymongo.MongoClient(mongo_uri)
db = client["analytics"]
app_collection = db["analytics"]
location_collection = db["locations"]
notification_collection = db["notifications"]
ist = pytz.timezone("Asia/Kolkata")

ITEMS_PER_PAGE = 15

# ── Helpers ──────────────────────────────────────────────────────────────────

@st.cache_data
def get_app_name_or_package(package_name):
    try:
        app_info = app(package_name, lang="en", country="in")
        return {'app_name': app_info['title'], 'app_image': app_info['icon']}
    except Exception:
        return {'app_name': package_name, 'app_image': None}


def format_time(milliseconds):
    return datetime.fromtimestamp(milliseconds / 1000).astimezone(ist).strftime("%d-%m-%Y %I:%M:%S %p")


def format_time_short(milliseconds):
    return datetime.fromtimestamp(milliseconds / 1000).astimezone(ist).strftime("%d %b %Y, %I:%M %p")


def get_duration(milliseconds):
    seconds = int(milliseconds / 1000)
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h {minutes % 60}m" if minutes % 60 else f"{hours}h"
    days = hours // 24
    if days < 30:
        return f"{days}d {hours % 24}h" if hours % 24 else f"{days}d"
    months = days // 30
    if months < 12:
        return f"{months}mo {days % 30}d" if days % 30 else f"{months}mo"
    years = months // 12
    return f"{years}y {months % 12}mo" if months % 12 else f"{years}y"


def get_notification_icon(package_name):
    """Return an emoji icon based on package name category."""
    icon_map = {
        "com.android.systemui": "🔋",
        "com.whatsapp": "💬",
        "com.google.android.gm": "📧",
        "com.google.android.apps.messaging": "💬",
        "com.instagram.android": "📷",
        "com.twitter.android": "🐦",
        "com.facebook.katana": "👤",
        "com.spotify.music": "🎵",
        "com.google.android.youtube": "▶️",
        "com.android.vending": "🛒",
        "com.google.android.apps.maps": "🗺️",
        "com.android.phone": "📞",
        "com.samsung.android.messaging": "💬",
        "com.samsung.android.dialer": "📞",
        "com.google.android.calendar": "📅",
        "com.android.chrome": "🌐",
        "com.google.android.apps.photos": "🖼️",
        "com.amazon.mShop.android.shopping": "🛍️",
        "com.phonepe.app": "💰",
        "com.google.android.apps.nbu.paisa.user": "💳",
        "in.amazon.mShop.android.shopping": "🛍️",
        "com.flipkart.android": "🛒",
        "com.truecaller": "📱",
    }
    for key, icon in icon_map.items():
        if key in package_name:
            return icon
    # Fallback based on broad categories
    if "message" in package_name.lower() or "chat" in package_name.lower() or "sms" in package_name.lower():
        return "💬"
    if "mail" in package_name.lower() or "email" in package_name.lower():
        return "📧"
    if "camera" in package_name.lower() or "photo" in package_name.lower():
        return "📷"
    if "music" in package_name.lower() or "audio" in package_name.lower():
        return "🎵"
    if "phone" in package_name.lower() or "dialer" in package_name.lower():
        return "📞"
    if "pay" in package_name.lower() or "bank" in package_name.lower() or "money" in package_name.lower():
        return "💰"
    return "🔔"


def paginate(key, total_items):
    """Render pagination controls and return (start_index, end_index)."""
    total_pages = max(1, math.ceil(total_items / ITEMS_PER_PAGE))

    if f"page_{key}" not in st.session_state:
        st.session_state[f"page_{key}"] = 1

    current_page = st.session_state[f"page_{key}"]
    current_page = min(current_page, total_pages)

    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ Previous", key=f"prev_{key}", disabled=(current_page <= 1), use_container_width=True):
            st.session_state[f"page_{key}"] = current_page - 1
            st.rerun()
    with col_info:
        st.markdown(
            f'<div class="pagination-info">Page {current_page} of {total_pages} &nbsp;·&nbsp; {total_items} items</div>',
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("Next ➡️", key=f"next_{key}", disabled=(current_page >= total_pages), use_container_width=True):
            st.session_state[f"page_{key}"] = current_page + 1
            st.rerun()

    start = (current_page - 1) * ITEMS_PER_PAGE
    end = min(start + ITEMS_PER_PAGE, total_items)
    return start, end


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
            reverse=True,
        )
        if usage_stats:
            processed_data.append({
                "current_time": current_time,
                "usage_stats": usage_stats,
            })
    return processed_data


def display_map(latitude, longitude, map_key="default"):
    icon = folium.Icon(icon="user", icon_color="white", color="blue", prefix="fa")
    location_map = folium.Map(location=[latitude, longitude], zoom_start=15)
    folium.Marker([latitude, longitude], icon=icon).add_to(location_map)
    return st_folium(location_map, width=725, height=450, key=f"map_{map_key}")


# ── Sidebar Navigation ──────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align:center; padding:1rem 0 0.5rem;">
    <span style="font-size:2rem;">📊</span>
    <div style="font-size:1.1rem; font-weight:700; color:#1a1a2e; margin-top:0.3rem;">Device Analytics</div>
    <div style="font-size:0.75rem; color:#888;">Real-time monitoring dashboard</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "📂 Navigation",
    ["🔔 Notifications", "📍 Locations", "📱 App Usage"],
    label_visibility="collapsed",
)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🔔 Notifications":
    st.markdown('<div class="page-title">🔔 Notifications</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">All captured notifications from connected devices</div>', unsafe_allow_html=True)

    # Fetch notifications
    notifications = list(notification_collection.find().sort("timestamp", -1))

    if not notifications:
        st.info("No notifications found.")
    else:
        # ── Filters ──
        with st.expander("🔍 Filters", expanded=False):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                # Unique device names
                device_names = sorted(set(n.get("deviceName", "Unknown") for n in notifications))
                selected_device = st.selectbox("📱 Device", ["All Devices"] + device_names, key="notif_device")
            with col_f2:
                # Unique package names
                package_names = sorted(set(n.get("package", "Unknown") for n in notifications))
                selected_package = st.selectbox("📦 Package", ["All Packages"] + package_names, key="notif_package")

        # Apply filters
        filtered = notifications
        if selected_device != "All Devices":
            filtered = [n for n in filtered if n.get("deviceName") == selected_device]
        if selected_package != "All Packages":
            filtered = [n for n in filtered if n.get("package") == selected_package]

        # ── Metric cards ──
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(filtered)}</div>
                <div class="metric-label">Total Notifications</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            unique_apps = len(set(n.get("package", "") for n in filtered))
            st.markdown(f"""
            <div class="metric-card green">
                <div class="metric-value">{unique_apps}</div>
                <div class="metric-label">Unique Apps</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m3:
            unique_devices = len(set(n.get("deviceId", "") for n in filtered))
            st.markdown(f"""
            <div class="metric-card blue">
                <div class="metric-value">{unique_devices}</div>
                <div class="metric-label">Devices</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Pagination ──
        start, end = paginate("notifications", len(filtered))

        # ── Render notification cards ──
        for notif in filtered[start:end]:
            pkg = notif.get("package", "Unknown")
            title = html_module.escape(str(notif.get("title", "")))
            text = html_module.escape(str(notif.get("text", "")))
            sub_text = html_module.escape(str(notif.get("subText", "")))
            timestamp = notif.get("timestamp", 0)
            device_name = html_module.escape(str(notif.get("deviceName", "Unknown")))
            time_str = format_time_short(timestamp) if timestamp else "—"

            # App name & icon lookup (same as App Usage page)
            app_info = get_app_name_or_package(pkg)
            app_name = html_module.escape(str(app_info['app_name']))
            app_image = app_info.get('app_image')

            # Use Play Store icon if available, otherwise fallback emoji
            if app_image:
                icon_html = f'<img src="{app_image}" style="width:42px;height:42px;border-radius:10px;object-fit:cover;" alt="{app_name}">'
            else:
                icon_html = f'<span style="font-size:2rem;">{get_notification_icon(pkg)}</span>'

            sub_html = f'<div class="notif-text" style="color:#aaa;font-size:0.82rem;">{sub_text}</div>' if sub_text else ""
            display_title = title if title else app_name

            card_html = (
                '<div class="notif-card">'
                f'<div class="notif-icon">{icon_html}</div>'
                '<div class="notif-body">'
                f'<div class="notif-title">{display_title}</div>'
                f'<div class="notif-text">{text}</div>'
                f'{sub_html}'
                '<div class="notif-meta">'
                f'<span>📱 {device_name}</span>'
                f'<span>📦 {app_name}</span>'
                f'<span>🕐 {time_str}</span>'
                '</div>'
                '</div>'
                '</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

        # Bottom pagination
        st.markdown("<br>", unsafe_allow_html=True)
        paginate("notifications_bottom", len(filtered))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LOCATIONS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📍 Locations":
    st.markdown('<div class="page-title">📍 Locations</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">GPS location history from connected devices</div>', unsafe_allow_html=True)

    locations = list(location_collection.find().sort("time", -1))

    if not locations:
        st.info("No location data found.")
    else:
        # ── Metric cards ──
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(locations)}</div>
                <div class="metric-label">Total Location Records</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            latest_time = format_time_short(locations[0]["time"]) if locations else "—"
            st.markdown(f"""
            <div class="metric-card green">
                <div class="metric-value" style="font-size:1.2rem;">{latest_time}</div>
                <div class="metric-label">Latest Record</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Pagination ──
        start, end = paginate("locations", len(locations))

        for idx, location in enumerate(locations[start:end]):
            latitude = location["latitude"]
            longitude = location["longitude"]
            loc_time = format_time(location["time"])

            with st.expander(f"📍 {format_time_short(location['time'])}", expanded=(idx == 0)):
                st.markdown(f"""
                <div class="card">
                    <div class="loc-stat">
                        <span class="loc-stat-icon">🌐</span>
                        <div>
                            <div class="loc-stat-label">Latitude</div>
                            <div class="loc-stat-value">{latitude}</div>
                        </div>
                    </div>
                    <div class="loc-stat">
                        <span class="loc-stat-icon">🌐</span>
                        <div>
                            <div class="loc-stat-label">Longitude</div>
                            <div class="loc-stat-value">{longitude}</div>
                        </div>
                    </div>
                    <div class="loc-stat">
                        <span class="loc-stat-icon">🕐</span>
                        <div>
                            <div class="loc-stat-label">Timestamp (IST)</div>
                            <div class="loc-stat-value">{loc_time}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    apple_maps_url = f"https://maps.apple.com/?q={latitude},{longitude}"
                    st.markdown(f"[🍎 Open in Apple Maps]({apple_maps_url})")
                with col_l2:
                    google_maps_url = f"https://www.google.com/maps/?q={latitude},{longitude}"
                    st.markdown(f"[🗺️ Open in Google Maps]({google_maps_url})")

                display_map(latitude, longitude, map_key=f"loc_{start + idx}")

        st.markdown("<br>", unsafe_allow_html=True)
        paginate("locations_bottom", len(locations))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: APP USAGE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📱 App Usage":
    st.markdown('<div class="page-title">📱 App Usage Stats</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Screen time and foreground usage analytics</div>', unsafe_allow_html=True)

    docs = list(app_collection.find().sort("currentTimestamp", -1))
    data = process_documents(docs)

    if not data:
        st.info("No app usage data found.")
    else:
        # Sidebar timestamp selector
        st.sidebar.markdown("---")
        st.sidebar.markdown("#### 🕐 Select Snapshot")
        selected_time = st.sidebar.radio(
            "Timestamp",
            [doc["current_time"] for doc in data],
            label_visibility="collapsed",
        )

        for doc in data:
            if doc["current_time"] == selected_time:
                usage = doc["usage_stats"]

                # ── Metrics ──
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{len(usage)}</div>
                        <div class="metric-label">Active Apps</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_m2:
                    total_time_ms = sum(s['totalTimeInForeground'] for s in usage)
                    st.markdown(f"""
                    <div class="metric-card green">
                        <div class="metric-value">{get_duration(total_time_ms)}</div>
                        <div class="metric-label">Total Screen Time</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_m3:
                    top_app = usage[0]['packageName'] if usage else "—"
                    st.markdown(f"""
                    <div class="metric-card orange">
                        <div class="metric-value" style="font-size:1rem;">{top_app}</div>
                        <div class="metric-label">Most Used App</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Pagination ──
                start, end = paginate("app_usage", len(usage))

                for row in usage[start:end]:
                    img_html = ""
                    if row.get("appImage"):
                        img_html = f'<div class="app-icon"><img src="{row["appImage"]}" alt="icon"></div>'
                    else:
                        img_html = '<div class="app-icon" style="font-size:2rem;">📱</div>'

                    st.markdown(f"""
                    <div class="app-row">
                        {img_html}
                        <div class="app-info">
                            <div class="app-name">{row['packageName']}</div>
                            <div class="app-detail">First: {row['firstTimeStamp']} · Last: {row['lastTimeStamp']}</div>
                        </div>
                        <div class="app-duration">{get_duration(row['totalTimeInForeground'])}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                paginate("app_usage_bottom", len(usage))

                # ── Chart ──
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 📊 Screen Time by App")
                df = pd.DataFrame(usage)
                df["duration_min"] = df["totalTimeInForeground"] / 60000
                chart_data = df.set_index("packageName")["duration_min"].head(20)
                st.bar_chart(chart_data)
                break
