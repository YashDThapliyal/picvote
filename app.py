import streamlit as st
from PIL import Image
import io
import uuid

# Initialize session state
if 'images' not in st.session_state:
    st.session_state.images = {}
if 'votes' not in st.session_state:
    st.session_state.votes = {}
if 'user' not in st.session_state:
    st.session_state.user = None

def main():
    st.title("Picture Voting Website")

    # User authentication
    if st.session_state.user is None:
        username = st.text_input("Enter your name to sign in")
        if st.button("Sign In"):
            if username:
                st.session_state.user = username
                st.success(f"Welcome, {username}!")
                st.experimental_rerun()
    else:
        st.sidebar.write(f"Signed in as: {st.session_state.user}")
        if st.sidebar.button("Sign Out"):
            st.session_state.user = None
            st.experimental_rerun()

    if st.session_state.user:
        # File uploader
        uploaded_file = st.file_uploader("Choose an image", type=["jpg", "png", "jpeg"])
        if uploaded_file is not None:
            if st.button("Upload Image"):
                # Generate a unique ID for the image
                image_id = str(uuid.uuid4())
                # Add image to session state
                image = Image.open(uploaded_file)
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                st.session_state.images[image_id] = {
                    'data': img_byte_arr.getvalue(),
                    'name': uploaded_file.name,
                    'uploader': st.session_state.user
                }
                st.session_state.votes[image_id] = 0
                st.success("Image uploaded successfully!")

        # Display images and voting
        st.subheader("Vote for Pictures")
        cols = st.columns(3)
        for idx, (image_id, image_info) in enumerate(st.session_state.images.items()):
            with cols[idx % 3]:
                image = Image.open(io.BytesIO(image_info['data']))
                st.image(image, caption=image_info['name'], use_column_width=True)
                st.write(f"Uploaded by: {image_info['uploader']}")
                st.write(f"Votes: {st.session_state.votes[image_id]}")
                if st.button(f"Vote", key=f"vote_{image_id}"):
                    st.session_state.votes[image_id] += 1
                    st.experimental_rerun()

        # Display vote results
        st.subheader("Voting Results")
        results = [{"Image": info['name'], "Uploader": info['uploader'], "Votes": st.session_state.votes[id]} 
                   for id, info in st.session_state.images.items()]
        results_sorted = sorted(results, key=lambda x: x['Votes'], reverse=True)
        st.table(results_sorted)

if __name__ == "__main__":
    main()
