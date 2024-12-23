import streamlit as st
import io
import uuid
from PIL import Image
from pillow_heif import register_heif_opener
from database import init_db

# Register HEIF opener to support HEIC files
register_heif_opener()

# Set page configuration
st.set_page_config(page_title="Picture Voting App", layout="wide")

# Custom CSS
def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# Initialize database
init_db()

# Database connection
conn = st.connection('sqlite', type='sql')

# Helper functions
def add_user(username):
    with conn.session as c:
        c.execute('INSERT INTO users (username) VALUES (?)', (username,))

def get_user_id(username):
    with conn.session as c:
        result = c.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    return result[0] if result else None

def create_session(name, host_id):
    session_id = str(uuid.uuid4())
    with conn.session as c:
        c.execute('INSERT INTO sessions (id, name, host_id) VALUES (?, ?, ?)', (session_id, name, host_id))
    return session_id

def get_active_sessions():
    return conn.query('SELECT s.id, s.name, u.username as host FROM sessions s JOIN users u ON s.host_id = u.id')

def add_image(session_id, name, data):
    with conn.session as c:
        c.execute('INSERT INTO images (session_id, name, data) VALUES (?, ?, ?)', (session_id, name, data))

def get_session_images(session_id):
    return conn.query('SELECT id, name FROM images WHERE session_id = ?', params=(session_id,))

def record_vote(user_id, image_id):
    with conn.session as c:
        c.execute('INSERT INTO votes (user_id, image_id) VALUES (?, ?)', (user_id, image_id))

def get_vote_count(image_id):
    result = conn.query('SELECT COUNT(*) as count FROM votes WHERE image_id = ?', params=(image_id,))
    return result.iloc[0]['count']

def user_has_voted(user_id, session_id):
    result = conn.query('''
        SELECT COUNT(*) as count 
        FROM votes v 
        JOIN images i ON v.image_id = i.id 
        WHERE v.user_id = ? AND i.session_id = ?
    ''', params=(user_id, session_id))
    return result.iloc[0]['count'] > 0

# Main app
def main():
    st.title("Picture Voting App")

    # User authentication
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    if st.session_state.user_id is None:
        with st.container():
            st.subheader("Sign In or Sign Up")
            username = st.text_input("Username")
            if st.button("Sign In / Sign Up"):
                user_id = get_user_id(username)
                if user_id is None:
                    add_user(username)
                    user_id = get_user_id(username)
                st.session_state.user_id = user_id
                st.success(f"Welcome, {username}!")
                st.rerun()

    else:
        user = conn.query('SELECT username FROM users WHERE id = ?', params=(st.session_state.user_id,)).iloc[0]
        st.sidebar.write(f"Signed in as: {user['username']}")
        if st.sidebar.button("Sign Out"):
            st.session_state.user_id = None
            st.rerun()

        # Session management
        if 'current_session' not in st.session_state:
            st.session_state.current_session = None

        if st.session_state.current_session is None:
            st.subheader("Join or Create a Session")
            col1, col2 = st.columns(2)
            with col1:
                session_name = st.text_input("Enter a name for your session")
                if st.button("Create New Session"):
                    if session_name:
                        session_id = create_session(session_name, st.session_state.user_id)
                        st.session_state.current_session = session_id
                        st.success(f"New session created: {session_name}")
                        st.rerun()
                    else:
                        st.error("Please enter a session name")

            with col2:
                st.subheader("Active Sessions")
                active_sessions = get_active_sessions()
                for _, session in active_sessions.iterrows():
                    with st.expander(f"{session['name']} (Host: {session['host']})"):
                        if st.button(f"Join Session", key=f"join_{session['id']}"):
                            st.session_state.current_session = session['id']
                            st.success(f"Joined session: {session['name']}")
                            st.rerun()

        else:
            session = conn.query('SELECT * FROM sessions WHERE id = ?', params=(st.session_state.current_session,)).iloc[0]
            st.subheader(f"Current Session: {session['name']}")
            host = conn.query('SELECT username FROM users WHERE id = ?', params=(session['host_id'],)).iloc[0]
            st.write(f"Host: {host['username']}")

            # File uploader (only for host)
            if st.session_state.user_id == session['host_id']:
                uploaded_files = st.file_uploader("Choose images", type=["jpg", "jpeg", "png", "heic"], accept_multiple_files=True)
                if uploaded_files:
                    if st.button("Upload Images"):
                        for uploaded_file in uploaded_files:
                            image_data = uploaded_file.read()
                            add_image(st.session_state.current_session, uploaded_file.name, image_data)
                        st.success(f"{len(uploaded_files)} image(s) uploaded successfully!")
                        st.rerun()

            # Display images and voting
            st.subheader("Vote for Pictures")
            session_images = get_session_images(st.session_state.current_session)
            cols = st.columns(3)
            for idx, image in session_images.iterrows():
                with cols[idx % 3]:
                    image_data = conn.query('SELECT data FROM images WHERE id = ?', params=(image['id'],)).iloc[0]['data']
                    img = Image.open(io.BytesIO(image_data))
                    st.image(img, caption=image['name'], use_column_width=True)
                    vote_count = get_vote_count(image['id'])
                    st.write(f"Votes: {vote_count}")
                    
                    # Check if user has already voted
                    if not user_has_voted(st.session_state.user_id, st.session_state.current_session):
                        if st.button(f"Vote", key=f"vote_{image['id']}"):
                            record_vote(st.session_state.user_id, image['id'])
                            st.success("Vote recorded!")
                            st.rerun()
                    else:
                        st.info("You have already voted in this session.")

            if st.button("Leave Session"):
                st.session_state.current_session = None
                st.rerun()

if __name__ == "__main__":
    main()
