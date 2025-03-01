import streamlit as st
import time
import random
import string
from datetime import datetime
import supabase

# Initialize Supabase client
def init_supabase():
    try:
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_key"]
        return supabase.create_client(url, key)
    except Exception as e:
        st.error(f"Failed to initialize Supabase: {str(e)}")
        st.info("Please make sure your .streamlit/secrets.toml file is correctly set up with Supabase credentials")
        return None

# Page configuration
st.set_page_config(
    page_title="RetroChat",
    page_icon="📺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False

# Generate a random room code
def generate_room_code():
    return ''.join(random.choices(string.digits, k=5))

# Create a new chatroom
def create_room(room_name, username):
    supabase_client = init_supabase()
    if not supabase_client:
        st.error("Cannot create room - database connection failed")
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
        st.session_state.db_connected = True
        
        return room_code
    except Exception as e:
        st.error(f"Error creating room: {str(e)}")
        return None

# Join an existing chatroom
def join_room(room_code, username):
    supabase_client = init_supabase()
    if not supabase_client:
        st.error("Cannot join room - database connection failed")
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
        st.session_state.db_connected = True
        
        return True
    except Exception as e:
        st.error(f"Error joining room: {str(e)}")
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
        st.error(f"Error approving user: {str(e)}")

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
        st.error(f"Error rejecting user: {str(e)}")

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
        st.error(f"Error sending message: {str(e)}")

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
            st.error(f"Error checking pending users: {str(e)}")

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
        st.error(f"Error fetching messages: {str(e)}")

# Leave the chatroom
def leave_room():
    if st.session_state.in_room:
        supabase_client = init_supabase()
        if not supabase_client:
            # Reset session state even if DB connection fails
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
            st.error(f"Error leaving room: {str(e)}")
        finally:
            # Reset session state
            reset_session_state()

def reset_session_state():
    st.session_state.username = ""
    st.session_state.room_code = ""
    st.session_state.is_host = False
    st.session_state.in_room = False
    st.session_state.pending_users = []
    st.session_state.messages = []
    st.session_state.last_message_time = datetime.now().isoformat()
    st.session_state.db_connected = False

# Main UI logic
def main():
    # Display header
    st.title("RetroChat")
    
    # Display app status - helpful for debugging
    if st.query_params.get("debug") == "true":
        st.sidebar.subheader("Debug Info")
        st.sidebar.write(f"Database Connected: {st.session_state.db_connected}")
        st.sidebar.write(f"In Room: {st.session_state.in_room}")
        st.sidebar.write(f"Is Host: {st.session_state.is_host}")
    
    # Check if user is in a room
    if st.session_state.in_room:
        display_chat_interface()
    else:
        display_entry_interface()

# Display the initial entry interface (create/join room)
def display_entry_interface():
    col1, col2 = st.columns(2)
    
    with col1:
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
        
    with col2:
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

# Display the chat interface
def display_chat_interface():
    # Check for pending users and new messages
    check_pending_users()
    get_new_messages()
    
    # Display room info
    st.info(f"Room Code: {st.session_state.room_code} | Logged in as: {st.session_state.username}")
    
    # Display pending user requests (for host only)
    if st.session_state.is_host and st.session_state.pending_users:
        st.subheader("Pending Requests")
        
        for user in st.session_state.pending_users:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(user)
            with col2:
                if st.button("Accept", key=f"accept_{user}", use_container_width=True):
                    approve_user(user)
                    st.experimental_rerun()
            with col3:
                if st.button("Reject", key=f"reject_{user}", use_container_width=True):
                    reject_user(user)
                    st.experimental_rerun()
    
    # Display chat messages
    st.subheader("Chat")
    chat_container = st.container(height=400)
    
    with chat_container:
        for msg in st.session_state.messages:
            if msg.get('is_system', False):
                st.warning(msg['message'])
            else:
                if msg['username'] == st.session_state.username:
                    st.success(f"**{msg['username']}**: {msg['message']}")
                    st.caption(f"{datetime.fromisoformat(msg['sent_at']).strftime('%H:%M:%S')}")
                else:
                    st.info(f"**{msg['username']}**: {msg['message']}")
                    st.caption(f"{datetime.fromisoformat(msg['sent_at']).strftime('%H:%M:%S')}")
    
    # Message input
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
    
    # Auto-refresh for real-time updates (less aggressive to prevent rate limiting)
    time.sleep(2)
    st.experimental_rerun()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Try refreshing the page or check your configuration.")
