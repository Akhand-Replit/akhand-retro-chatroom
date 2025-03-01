import streamlit as st
import time
import random
import string
from datetime import datetime
import supabase

# Initialize Supabase client
def init_supabase():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    return supabase.create_client(url, key)

# Page configuration
st.set_page_config(
    page_title="RetroChat",
    page_icon="📺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Load custom CSS for retro styling
def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Try to load CSS, create the file if it doesn't exist
try:
    load_css()
except FileNotFoundError:
    with open("styles.css", "w") as f:
        f.write("""
        /* Retro styling will be added here */
        """)
    load_css()

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
    room_code = generate_room_code()
    
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

# Join an existing chatroom
def join_room(room_code, username):
    supabase_client = init_supabase()
    
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

# Approve a user to join the room
def approve_user(username):
    supabase_client = init_supabase()
    
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

# Reject a user from joining the room
def reject_user(username):
    supabase_client = init_supabase()
    
    # Remove from pending
    supabase_client.table('pending_users').delete().match({
        'room_code': st.session_state.room_code,
        'username': username
    }).execute()
    
    # Remove from pending users list in session state
    st.session_state.pending_users.remove(username)

# Send a message to the chatroom
def send_message(room_code, username, message, is_system=False):
    supabase_client = init_supabase()
    
    # Insert message into Supabase
    supabase_client.table('messages').insert({
        'room_code': room_code,
        'username': username,
        'message': message,
        'is_system': is_system,
        'sent_at': datetime.now().isoformat()
    }).execute()

# Check for pending users (for host)
def check_pending_users():
    if st.session_state.is_host:
        supabase_client = init_supabase()
        
        # Get pending users
        result = supabase_client.table('pending_users').select('username').eq('room_code', st.session_state.room_code).execute()
        
        # Update pending users list
        pending = [user['username'] for user in result.data]
        st.session_state.pending_users = pending

# Get new messages
def get_new_messages():
    supabase_client = init_supabase()
    
    # Get messages newer than the last one we've seen
    result = supabase_client.table('messages').select('*').eq('room_code', st.session_state.room_code).gt('sent_at', st.session_state.last_message_time).order('sent_at').execute()
    
    if len(result.data) > 0:
        # Update last message time
        st.session_state.last_message_time = result.data[-1]['sent_at']
        
        # Add new messages to state
        st.session_state.messages.extend(result.data)

# Leave the chatroom
def leave_room():
    if st.session_state.in_room:
        supabase_client = init_supabase()
        
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
        
        # Reset session state
        st.session_state.username = ""
        st.session_state.room_code = ""
        st.session_state.is_host = False
        st.session_state.in_room = False
        st.session_state.pending_users = []
        st.session_state.messages = []
        st.session_state.last_message_time = datetime.now().isoformat()

# Main UI logic
def main():
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
