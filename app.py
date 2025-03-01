import streamlit as st
import time
import random
import string
from datetime import datetime
import os
import json
try:
    from supabase import create_client, Client
except ImportError:
    # If import fails, show helpful error message
    st.error("Missing required package. Please run: pip install supabase")
    st.stop()

# Initialize Supabase client
def init_supabase():
    try:
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Failed to initialize Supabase: {str(e)}")
        st.info("Please make sure you've added your Supabase URL and key to the Streamlit secrets.")
        return None

# Page configuration
st.set_page_config(
    page_title="RetroChat",
    page_icon="📺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Load custom CSS for retro styling
def load_css():
    # Embed the CSS directly in the Python file to avoid file path issues
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

    /* Base styling and animations */
    @keyframes scanline {
      0% {
        transform: translateY(0);
      }
      100% {
        transform: translateY(100vh);
      }
    }

    @keyframes glow {
      0% {
        text-shadow: 0 0 5px #ff00ff, 0 0 10px #ff00ff, 0 0 15px #ff00ff;
      }
      50% {
        text-shadow: 0 0 10px #ff00ff, 0 0 20px #ff00ff, 0 0 30px #ff00ff;
      }
      100% {
        text-shadow: 0 0 5px #ff00ff, 0 0 10px #ff00ff, 0 0 15px #ff00ff;
      }
    }

    @keyframes textGlitch {
      0% {
        opacity: 1;
        transform: translateX(0) skewX(0);
      }
      10% {
        opacity: 0.8;
        transform: translateX(-2px) skewX(3deg);
      }
      13% {
        opacity: 1;
        transform: translateX(0) skewX(0);
      }
      20% {
        opacity: 1;
        transform: translateX(0) skewX(0);
      }
      30% {
        opacity: 0.7;
        transform: translateX(3px) skewX(-3deg);
      }
      33% {
        opacity: 1;
        transform: translateX(0) skewX(0);
      }
      100% {
        opacity: 1;
        transform: translateX(0) skewX(0);
      }
    }

    /* Global styles */
    body {
      font-family: 'VT323', monospace;
      background-color: #120458;
      color: #00ffff;
      font-size: 18px;
      position: relative;
      overflow-x: hidden;
    }

    /* Override some Streamlit defaults */
    .stApp {
      background: linear-gradient(180deg, #120458 0%, #000000 100%);
    }

    .stButton > button {
      font-family: 'Press Start 2P', cursive;
      background: #ff00ff;
      color: #000000;
      border: 3px solid #00ffff;
      box-shadow: 0 0 10px #00ffff, 0 0 20px rgba(0, 255, 255, 0.5);
      font-weight: bold;
      transition: all 0.3s;
    }

    .stButton > button:hover {
      background: #00ffff;
      color: #000000;
      border-color: #ff00ff;
      box-shadow: 0 0 15px #ff00ff, 0 0 30px rgba(255, 0, 255, 0.5);
      transform: scale(1.05);
    }

    /* Input styling */
    .stTextInput > div > div > input {
      font-family: 'VT323', monospace;
      background-color: rgba(0, 0, 0, 0.7);
      color: #00ffff;
      border: 2px solid #ff00ff;
      box-shadow: 0 0 8px #ff00ff;
      padding: 10px;
      font-size: 20px;
      margin-bottom: 10px;
    }

    .stTextInput > div > div > input:focus {
      border-color: #00ffff;
      box-shadow: 0 0 12px #00ffff;
    }

    .stTextInput > div > label {
      font-family: 'Press Start 2P', cursive;
      color: #ff00ff;
      font-size: 14px;
      text-shadow: 0 0 5px #ff00ff;
    }

    /* Header styling */
    .retro-header {
      text-align: center;
      margin-bottom: 30px;
      position: relative;
    }

    .retro-header h1 {
      font-family: 'Press Start 2P', cursive;
      color: #00ffff;
      font-size: 48px;
      text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff;
      animation: glow 2s infinite;
      margin: 20px 0;
      letter-spacing: 2px;
    }

    .scanline {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 5px;
      background: rgba(0, 255, 255, 0.3);
      opacity: 0.7;
      animation: scanline 3s linear infinite;
      pointer-events: none;
      z-index: 100;
    }

    /* Entry interface styling */
    .entry-container {
      display: flex;
      flex-direction: column;
      position: relative;
      margin-top: 20px;
    }

    .option-box {
      background: rgba(0, 0, 0, 0.7);
      border: 3px solid;
      padding: 20px;
      border-radius: 5px;
      margin-bottom: 20px;
      position: relative;
      overflow: hidden;
    }

    .host-box {
      border-color: #ff00ff;
      box-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
    }

    .join-box {
      border-color: #00ffff;
      box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
    }

    .crt-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: repeating-linear-gradient(
        0deg,
        rgba(0, 0, 0, 0.1),
        rgba(0, 0, 0, 0.1) 1px,
        transparent 1px,
        transparent 2px
      );
      pointer-events: none;
      z-index: 999;
    }

    /* Chat interface styling */
    .room-info {
      font-family: 'Press Start 2P', cursive;
      background: rgba(0, 0, 0, 0.7);
      border: 2px solid #ff00ff;
      padding: 10px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 14px;
    }

    .code-display {
      color: #00ffff;
      font-size: 18px;
      text-shadow: 0 0 5px #00ffff;
      letter-spacing: 2px;
    }

    .user-highlight {
      color: #ff00ff;
      font-size: 16px;
      text-shadow: 0 0 5px #ff00ff;
    }

    .pending-requests {
      background: rgba(0, 0, 0, 0.7);
      border: 2px solid #ffff00;
      padding: 15px;
      margin-bottom: 20px;
    }

    .pending-requests h3 {
      font-family: 'Press Start 2P', cursive;
      color: #ffff00;
      font-size: 16px;
      text-shadow: 0 0 5px #ffff00;
      margin-bottom: 15px;
    }

    .pending-user {
      font-family: 'VT323', monospace;
      color: #ffff00;
      font-size: 22px;
      padding: 5px 0;
    }

    .chat-container {
      background: rgba(0, 0, 0, 0.7);
      border: 2px solid #00ffff;
      height: 400px;
      overflow-y: auto;
      padding: 15px;
      margin-bottom: 20px;
      box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
    }

    .message {
      margin-bottom: 15px;
      padding: 10px;
      border-radius: 5px;
      max-width: 80%;
      position: relative;
      animation: textGlitch 5s infinite;
      animation-delay: calc(var(--index, 0) * 1s);
    }

    .self-message {
      background: rgba(255, 0, 255, 0.2);
      border-left: 3px solid #ff00ff;
      margin-left: auto;
    }

    .other-message {
      background: rgba(0, 255, 255, 0.2);
      border-left: 3px solid #00ffff;
      margin-right: auto;
    }

    .system-message {
      background: rgba(255, 255, 0, 0.2);
      border-left: 3px solid #ffff00;
      margin: 10px auto;
      width: 90%;
      text-align: center;
      animation: textGlitch 8s infinite;
    }

    .message-sender {
      font-family: 'Press Start 2P', cursive;
      font-size: 12px;
      color: #ff00ff;
      margin-bottom: 5px;
    }

    .message-content {
      font-family: 'VT323', monospace;
      font-size: 20px;
      word-break: break-word;
    }

    .message-time {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.6);
      text-align: right;
      margin-top: 5px;
    }

    .message-input-container {
      margin-top: 10px;
    }

    /* Mobile responsiveness */
    @media (max-width: 768px) {
      .retro-header h1 {
        font-size: 36px;
      }
      
      .room-info {
        flex-direction: column;
        gap: 10px;
      }
      
      .message {
        max-width: 90%;
      }
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'room_code' not in st.session_state:
    st.session_state.room_code = ""
if 'is_host' not in st.session_state:
    st.session_state.is_host = False
if 'in_room' not in st.session_state:
    st.session_state.in_room = False
if 'pending_users' not in st.session_state:
    st.session_state.pending_users = []
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'last_message_time' not in st.session_state:
    st.session_state.last_message_time = datetime.now().isoformat()

# Generate a random room code
def generate_room_code():
    return ''.join(random.choices(string.digits, k=5))

# Create a new chatroom
def create_room(room_name, username):
    supabase_client = init_supabase()
    if not supabase_client:
        st.error("Could not connect to database. Please check your configuration.")
        return None
        
    room_code = generate_room_code()
    
    try:
        # Insert room data into Supabase
        supabase_client.table('rooms').insert({
            'code': room_code,
            'name': room_name,
            'host': username,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        # Set session state
        st.session_state.username = username
        st.session_state.room_code = room_code
        st.session_state.is_host = True
        st.session_state.in_room = True
        
        return room_code
    except Exception as e:
        st.error(f"Failed to create room: {str(e)}")
        return None

# Join an existing chatroom
def join_room(room_code, username):
    supabase_client = init_supabase()
    if not supabase_client:
        st.error("Could not connect to database. Please check your configuration.")
        return False
    
    try:
        # Check if room exists
        result = supabase_client.table('rooms').select('*').eq('code', room_code).execute()
        
        if len(result.data) == 0:
            st.error("Room not found!", icon="🚫")
            return False
        
        # If room exists, add user to pending list
        supabase_client.table('pending_users').insert({
            'room_code': room_code,
            'username': username,
            'requested_at': datetime.now().isoformat()
        }).execute()
        
        # Set session state
        st.session_state.username = username
        st.session_state.room_code = room_code
        
        return True
    except Exception as e:
        st.error(f"Failed to join room: {str(e)}")
        return False

# Approve a user to join the room
def approve_user(username):
    supabase_client = init_supabase()
    if not supabase_client:
        return
    
    try:
        # Remove from pending and add to approved users
        supabase_client.table('pending_users').delete().match({
            'room_code': st.session_state.room_code,
            'username': username
        }).execute()
        
        supabase_client.table('room_users').insert({
            'room_code': st.session_state.room_code,
            'username': username,
            'joined_at': datetime.now().isoformat()
        }).execute()
        
        # Add system message about user joining
        send_message(st.session_state.room_code, "SYSTEM", f"{username} has joined the chatroom", is_system=True)
        
        # Remove from pending users list in session state
        st.session_state.pending_users.remove(username)
    except Exception as e:
        st.error(f"Failed to approve user: {str(e)}")

# Reject a user from joining the room
def reject_user(username):
    supabase_client = init_supabase()
    if not supabase_client:
        return
    
    try:
        # Remove from pending
        supabase_client.table('pending_users').delete().match({
            'room_code': st.session_state.room_code,
            'username': username
        }).execute()
        
        # Remove from pending users list in session state
        st.session_state.pending_users.remove(username)
    except Exception as e:
        st.error(f"Failed to reject user: {str(e)}")

# Send a message to the chatroom
def send_message(room_code, username, message, is_system=False):
    supabase_client = init_supabase()
    if not supabase_client:
        return
    
    try:
        # Insert message into Supabase
        supabase_client.table('messages').insert({
            'room_code': room_code,
            'username': username,
            'message': message,
            'is_system': is_system,
            'sent_at': datetime.now().isoformat()
        }).execute()
    except Exception as e:
        st.error(f"Failed to send message: {str(e)}")

# Check for pending users (for host)
def check_pending_users():
    if st.session_state.is_host:
        supabase_client = init_supabase()
        if not supabase_client:
            return
        
        try:
            # Get pending users
            result = supabase_client.table('pending_users').select('username').eq('room_code', st.session_state.room_code).execute()
            
            # Update pending users list
            pending = [user['username'] for user in result.data]
            st.session_state.pending_users = pending
        except Exception as e:
            st.error(f"Failed to check pending users: {str(e)}")

# Get new messages
def get_new_messages():
    supabase_client = init_supabase()
    if not supabase_client:
        return
    
    try:
        # Get messages newer than the last one we've seen
        result = supabase_client.table('messages').select('*').eq('room_code', st.session_state.room_code).gt('sent_at', st.session_state.last_message_time).order('sent_at').execute()
        
        if len(result.data) > 0:
            # Update last message time
            st.session_state.last_message_time = result.data[-1]['sent_at']
            
            # Add new messages to state
            st.session_state.messages.extend(result.data)
    except Exception as e:
        st.error(f"Failed to get new messages: {str(e)}")

# Leave the chatroom
def leave_room():
    if st.session_state.in_room:
        supabase_client = init_supabase()
        if not supabase_client:
            # Reset session state even if Supabase connection fails
            reset_session_state()
            return
            
        try:
            # If user was approved to room, send exit message
            result = supabase_client.table('room_users').select('*').match({
                'room_code': st.session_state.room_code,
                'username': st.session_state.username
            }).execute()
            
            if len(result.data) > 0 or st.session_state.is_host:
                # Send system message about user leaving
                send_message(st.session_state.room_code, "SYSTEM", f"{st.session_state.username} has left the chatroom", is_system=True)
            
            # If host, delete room and all associated data
            if st.session_state.is_host:
                # Delete room and cascade to all related data
                supabase_client.table('rooms').delete().eq('code', st.session_state.room_code).execute()
            else:
                # Just remove the user from room_users
                supabase_client.table('room_users').delete().match({
                    'room_code': st.session_state.room_code,
                    'username': st.session_state.username
                }).execute()
        except Exception as e:
            st.error(f"Failed to properly leave room: {str(e)}")
        finally:
            # Always reset session state
            reset_session_state()

# Reset session state
def reset_session_state():
    st.session_state.username = ""
    st.session_state.room_code = ""
    st.session_state.is_host = False
    st.session_state.in_room = False
    st.session_state.pending_users = []
    st.session_state.messages = []
    st.session_state.last_message_time = datetime.now().isoformat()

# Main UI logic
def main():
    # Load CSS
    load_css()
    
    # Add debug information (temporary, can be removed later)
    if st.query_params.get("debug"):
        st.sidebar.title("Debug Info")
        st.sidebar.write("Session State:")
        st.sidebar.write(st.session_state)
        
        try:
            if "supabase_url" in st.secrets:
                st.sidebar.success("Supabase URL found in secrets")
            else:
                st.sidebar.error("No Supabase URL in secrets")
                
            if "supabase_key" in st.secrets:
                st.sidebar.success("Supabase key found in secrets")
            else:
                st.sidebar.error("No Supabase key in secrets")
        except:
            st.sidebar.error("Could not access secrets")
    
    # Display the retro header
    st.markdown("""
    <div class="retro-header">
        <h1>RetroChat</h1>
        <div class="scanline"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if user is in a room
    if st.session_state.in_room:
        display_chat_interface()
    else:
        display_entry_interface()

# Display the initial entry interface (create/join room)
def display_entry_interface():
    st.markdown("""
    <div class="entry-container">
        <div class="crt-overlay"></div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="option-box host-box">', unsafe_allow_html=True)
        st.subheader("Host a Chatroom")
        room_name = st.text_input("Chatroom Name", key="host_room_name", 
                                  placeholder="Enter a room name...")
        username = st.text_input("Your Username", key="host_username", 
                                 placeholder="Enter your username...")
        
        if st.button("Create Room", key="create_room_btn", use_container_width=True):
            if room_name and username:
                room_code = create_room(room_name, username)
                if room_code:
                    st.success(f"Room created! Code: {room_code}")
                    st.experimental_rerun()
            else:
                st.warning("Please enter both room name and username", icon="⚠️")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="option-box join-box">', unsafe_allow_html=True)
        st.subheader("Join a Chatroom")
        room_code = st.text_input("Room Code", key="join_room_code", 
                                  placeholder="Enter 5-digit code...")
        username = st.text_input("Your Username", key="join_username", 
                                 placeholder="Enter your username...")
        
        if st.button("Join Room", key="join_room_btn", use_container_width=True):
            if room_code and username:
                if join_room(room_code, username):
                    st.info("Request sent! Waiting for host approval...")
                    time.sleep(2)  # Give the user a moment to read the message
                    st.experimental_rerun()
            else:
                st.warning("Please enter both room code and username", icon="⚠️")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Display the chat interface
def display_chat_interface():
    # Check for pending users and new messages
    check_pending_users()
    get_new_messages()
    
    # Display room info
    st.markdown(f"""
    <div class="room-info">
        <div class="room-code">Room Code: <span class="code-display">{st.session_state.room_code}</span></div>
        <div class="username-display">Logged in as: <span class="user-highlight">{st.session_state.username}</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display pending user requests (for host only)
    if st.session_state.is_host and st.session_state.pending_users:
        st.markdown('<div class="pending-requests">', unsafe_allow_html=True)
        st.subheader("Pending Requests")
        
        for user in st.session_state.pending_users:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"<div class='pending-user'>{user}</div>", unsafe_allow_html=True)
            with col2:
                if st.button("Accept", key=f"accept_{user}", use_container_width=True):
                    approve_user(user)
                    st.experimental_rerun()
            with col3:
                if st.button("Reject", key=f"reject_{user}", use_container_width=True):
                    reject_user(user)
                    st.experimental_rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display chat messages
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for msg in st.session_state.messages:
        if msg.get('is_system', False):
            st.markdown(f"""
            <div class="message system-message">
                <div class="message-content">{msg['message']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="message {'self-message' if msg['username'] == st.session_state.username else 'other-message'}">
                <div class="message-sender">{msg['username']}</div>
                <div class="message-content">{msg['message']}</div>
                <div class="message-time">{datetime.fromisoformat(msg['sent_at']).strftime('%H:%M:%S')}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Message input
    st.markdown('<div class="message-input-container">', unsafe_allow_html=True)
    message = st.text_input("", key="message_input", placeholder="Type your message here...")
    col1, col2 = st.columns([5, 1])
    
    with col1:
        if st.button("Send", key="send_btn", use_container_width=True):
            if message:
                send_message(st.session_state.room_code, st.session_state.username, message)
                # Clear the input
                st.session_state.message_input = ""
                st.experimental_rerun()
    
    with col2:
        if st.button("Leave", key="leave_btn", use_container_width=True):
            leave_room()
            st.experimental_rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-refresh for real-time updates
    time.sleep(1)
    st.experimental_rerun()

if __name__ == "__main__":
    main()
