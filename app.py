import streamlit as st
from PIL import Image
import io
import uuid
import random
import string

# Initialize session state
if 'sessions' not in st.session_state:
    st.session_state.sessions = {}
if 'current_session' not in st.session_state:
    st.session_state.current_session = None
if 'user' not in st.session_state:
    st.session_state.user = None

def generate_session_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def main():
    st.title("Picture Voting Website")

    # User authentication
    if st.session_state.user is None:
        username = st.text_input("Enter your name to sign in")
        if st.button("Sign In"):
            if username:
                st.session_state.user = username
                st.success(f"Welcome, {username}!")
                st.rerun()

    if st.session_state.user:
        st.sidebar.write(f"Signed in as: {st.session_state.user}")
        if st.sidebar.button("Sign Out"):
            st.session_state.user = None
            st.session_state.current_session = None
            st.rerun()

        # Session management
        if st.session_state.current_session is None:
            st.subheader("Join or Create a Session")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create New Session"):
                    session_id = generate_session_id()
                    st.session_state.sessions[session_id] = {
                        'host': st.session_state.user,
                        'images': {},
                        'votes': {}
                    }
                    st.session_state.current_session = session_id
                    st.success(f"New session created! Session ID: {session_id}")
                    st.rerun()
            with col2:
                join_session_id = st.text_input("Enter Session ID to join")
                if st.button("Join Session"):
                    if join_session_id in st.session_state.sessions:
                        st.session_state.current_session = join_session_id
                        st.success(f"Joined session: {join_session_id}")
                        st.rerun()
                    else:
                        st.error("Invalid Session ID")
        else:
            session = st.session_state.sessions[st.session_state.current_session]
            st.subheader(f"Current Session: {st.session_state.current_session}")
            st.write(f"Host: {session['host']}")

            # File uploader (only for host)
            if st.session_state.user == session['host']:
                uploaded_file = st.file_uploader("Choose an image", type=["jpg", "png", "jpeg"])
                if uploaded_file is not None:
                    if st.button("Upload Image"):
                        image_id = str(uuid.uuid4())
                        image = Image.open(uploaded_file)
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        session['images'][image_id] = {
                            'data': img_byte_arr.getvalue(),
                            'name': uploaded_file.name,
                        }
                        session['votes'][image_id] = 0
                        st.success("Image uploaded successfully!")
                        st.rerun()

            # Display images and voting
            st.subheader("Vote for Pictures")
            cols = st.columns(3)
            for idx, (image_id, image_info) in enumerate(session['images'].items()):
                with cols[idx % 3]:
                    image = Image.open(io.BytesIO(image_info['data']))
                    st.image(image, caption=image_info['name'], use_column_width=True)
                    st.write(f"Votes: {session['votes'][image_id]}")
                    if st.button(f"Vote", key=f"vote_{image_id}"):
                        session['votes'][image_id] += 1
                        st.rerun()

            # Display vote results
            st.subheader("Voting Results")
            results = [{"Image": info['name'], "Votes": session['votes'][id]} 
                       for id, info in session['images'].items()]
            results_sorted = sorted(results, key=lambda x: x['Votes'], reverse=True)
            st.table(results_sorted)

            if st.button("Leave Session"):
                st.session_state.current_session = None
                st.rerun()

if __name__ == "__main__":
    main()
