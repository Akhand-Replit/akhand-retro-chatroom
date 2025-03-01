# RetroChat

A temporary chatroom application with a retro, 80s/90s inspired UI/UX design. Built with Streamlit and Supabase, featuring real-time messaging, user management, and nostalgic visual effects like neon colors, pixelated fonts, and VHS glitch animations.



## Features

- **Host a Chatroom**: Create a room with a unique 5-digit code
- **Join a Chatroom**: Enter a room code and wait for host approval
- **Real-Time Messaging**: Instant message delivery with retro styling
- **User Approval System**: Hosts can approve or reject join requests
- **Exit Notifications**: System messages when users leave
- **Retro UI Elements**: Neon colors, pixelated fonts, CRT effects, and more!

## Tech Stack

- **Frontend & Backend**: Streamlit (Python)
- **Database & Real-time Chat**: Supabase
- **Styling**: Custom CSS with retro aesthetics

## Setup Instructions

### 1. Prerequisites

- GitHub account
- [Streamlit Community Cloud](https://streamlit.io/cloud) account
- [Supabase](https://supabase.com/) account

### 2. Supabase Setup

1. Create a new Supabase project
2. Navigate to the SQL Editor in your Supabase dashboard
3. Copy the contents of `supabase_setup.sql` and run it in the SQL Editor
4. Go to Project Settings > API and note your Supabase URL and anon/public key

### 3. GitHub Repository Setup

1. Create a new GitHub repository for your project
2. Add all the files from this project to your repository:
   - `app.py` (main application file with embedded CSS)
   - `requirements.txt` (dependencies)
   - `.streamlit/config.toml` (Streamlit configuration)
   - `supabase_setup.sql` (database setup)
   - `README.md` (this documentation)
   - `.gitignore` (git ignore configuration)

### 4. Streamlit Cloud Deployment

1. Log in to [Streamlit Community Cloud](https://streamlit.io/cloud)
2. Click "New app" and select your GitHub repository
3. Select the main branch and set the main file path to `app.py`
4. Under "Advanced settings", add your Supabase secrets:
   - `supabase_url`: Your Supabase project URL
   - `supabase_key`: Your Supabase anon/public key
5. Click "Deploy"

## Usage Guide

### Hosting a Chatroom

1. Enter a chatroom name and your username
2. Click "Create Room"
3. Share the 5-digit code with others

### Joining a Chatroom

1. Enter the 5-digit code and your username
2. Click "Join Room"
3. Wait for the host to approve your request

### Using the Chat

- Type your message and click "Send"
- System notifications will appear when users join or leave
- Click "Leave" to exit the chatroom

## Troubleshooting

If you encounter a blank screen after deployment:

1. **Check Supabase Connection**: Add `?debug=true` to your app URL to see connection status
2. **Verify Secrets**: Ensure that your Supabase URL and key are correctly set in Streamlit Cloud
3. **Check Logs**: Review deployment logs in Streamlit Cloud dashboard for any errors

## Customization

- **Modify Colors**: Edit the CSS variables in the `load_css()` function
- **Add Sound Effects**: Implement sounds using Streamlit's audio components
- **New Features**: Extend functionality in `app.py`

## License

This project is available under the MIT License.

## Acknowledgements

- Fonts: [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P) and [VT323](https://fonts.google.com/specimen/VT323)
- Streamlit for making Python web apps easy
- Supabase for real-time database functionality
