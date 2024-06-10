import streamlit as st
import instaloader
import requests
from PIL import Image, ImageOps
import io
import base64
from streamlit_option_menu import option_menu


def get_instagram_media(post_url):
    load = instaloader.Instaloader()

    shortcode = post_url.split("/")[-2]
    if len(shortcode) < 3:
        shortcode = post_url.split("/")[-1]

    media_urls = []
    media_types = []

    try:
        post = instaloader.Post.from_shortcode(context=load.context, shortcode=shortcode)

        # Carousel
        if post.typename == 'GraphSidecar':
            for car in post.get_sidecar_nodes():
                if car.is_video:
                    media_urls.append(car.video_url)
                    media_types.append('mp4')
                else:
                    media_urls.append(car.display_url)
                    media_types.append('jpg')

        # Video
        elif post.is_video:
            media_urls.append(post.video_url)
            media_types.append('mp4')

        # Image
        else:
            media_urls.append(post.url)
            media_types.append('jpg')

        return media_urls, media_types

    except Exception as e:
        # st.error(f"Error: {e}")
        return None, None


def download_media(url, type, session_counter, index):
    # Download media and return as bytes.
    response = requests.get(url)
    if response.status_code == 200:
        media_bytes = response.content
        if type == 'jpg':
            filename = f"image_{session_counter}_{index}.jpg"
        else:
            filename = f"image_{session_counter}_{index}.mp4"
        return media_bytes, filename
    else:
        return None, None


def is_url_valid(url):
    # Check if the URL is valid and accessible
    try:
        response = requests.head(url)
        return response.status_code == 200
    except Exception:
        return False


def resize_and_pad_image(image_bytes, size=(200, 200)):
    # Resize and pad image to the specified size
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail(size)
    delta_width = size[0] - img.size[0]
    delta_height = size[1] - img.size[1]
    pad_width = delta_width // 2
    pad_height = delta_height // 2
    padding = (pad_width, pad_height, delta_width - pad_width, delta_height - pad_height)
    return ImageOps.expand(img, padding, fill='black')


def add_bg_from_local(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/jpeg;base64,{encoded});
            background-size: cover;
            text-align: center;
        }}
        .rounded-image img {{
            border-radius: 15px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def main():
    # Add background image
    add_bg_from_local('bg.jpg')  # Replace with your image file path

    # Custom CSS to hide Streamlit link button
    st.markdown("""
            <style>
            display: flex;
            justify-content: center;
            </style>
            """, unsafe_allow_html=True)

    with st.sidebar:
        selected = option_menu(
            menu_title=None,
            options=["Home", "About", "Privacy Policy", "Terms & Conditions"],
        )

    if selected == "Home":

        # Select page navigation
        options = ["Photo", "Reels", "Carousel"]
        icons = ["camera-fill", "camera-reels", "caret-right-square-fill"]
        selected_page = option_menu(
            menu_title=None,
            options=options,
            icons=icons,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#ffb3d1"},
                "icon": {"font-size": "16px", "color": "white"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "center",
                    "margin": "0px",
                    "--hover-color": "#ededed",
                    "color": "black"
                },
                "nav-link-selected": {"background-color": "#FF4B4B", "color": "white"}
            }
        )

        # Streamlit App
        st.title('Instagram Media Downloader')
        st.subheader('Download Videos, Reels, Photos from Instagram')

        if selected_page in options:

            # Hide Full Screen
            hide_img_fs = '''
            <style>
            button[title="View fullscreen"]{
                visibility: hidden;}
            </style>
            '''

            st.markdown(hide_img_fs, unsafe_allow_html=True)

            # Initialize session state
            if 'counter' not in st.session_state:
                st.session_state.counter = 1

            # Input for Instagram Post URL
            post_url = st.text_input("Enter Instagram Post URL:", key="input_url")

            # Automatically process when URL changes
            if st.session_state.input_url:
                # Exception Handling
                try:
                    # Loading Animation
                    with st.spinner('Downloading media...'):

                        media_urls, media_types = get_instagram_media(post_url)
                        # Decide Preview
                        if media_urls:
                            # Custom CSS to center media previews
                            st.markdown(
                                """
                                <style>
                                .centered-content {
                                    display: flex;
                                    justify-content: center;
                                    flex-wrap: wrap;
                                }
                                .centered-content > div {
                                    margin: 10px;
                                    text-align: center;
                                .media-container {
                                    position: relative;
                                    text-align: center;
                                }
                                .media-preview {
                                    display: block;
                                    margin: 0 auto;
                                    margin-bottom: 10px;
                                   
                                }
                                </style>
                                """,
                                unsafe_allow_html=True
                            )


                            # Center
                            st.markdown('<div class="centered-content">', unsafe_allow_html=True)

                            num_media = len(media_urls)
                            num_columns = min(num_media, 3)
                            num_rows = (num_columns + num_media - 1) // num_columns
                            # Display Preview
                            for row in range(num_rows):
                                cols = st.columns(num_columns)
                                for col_index in range(num_columns):
                                    index = row * num_columns + col_index
                                    if index < num_media:
                                        with cols[col_index]:
                                            # st.write(f"Media Preview {index + 1}:")
                                            media_bytes, filename = download_media(media_urls[index],
                                                                                   media_types[index],
                                                                                   st.session_state.counter, index + 1)

                                            if media_bytes:

                                                if media_types[index] == 'jpg':
                                                    # Resize and pad image
                                                    resized_img = resize_and_pad_image(media_bytes)
                                                    # st.image(resized_img, width=200, clamp=True)

                                                    st.markdown(
                                                        f'<div><img src="data:image/jpeg;base64,{base64.b64encode(media_bytes).decode()}" width="200" /></div>',
                                                        unsafe_allow_html=True)

                                                elif media_types[index] == 'mp4':
                                                    st.write(
                                                        f'<video width="300" height="300" controls><source src="data:video/mp4;base64,{base64.b64encode(media_bytes).decode()}" type="video/mp4"></video>',
                                                        unsafe_allow_html=True
                                                    )
                                                    # st.video(media_bytes, format="video/mp4", start_time=0)

                                                # Download Button
                                                # st.download_button(
                                                #     label=f"Download",
                                                #     data=media_bytes,
                                                #     file_name=filename,
                                                #     mime=f"image/{media_types[index]}" if media_types[
                                                #                                               index] == 'jpg' else f"video/{media_types[index]}"
                                                # )
                                                st.markdown(
                                                    """
                                                    <style>
                                                    .download-button {
                                                        background-color: #FF4B4B;
                                                        color: white;
                                                        border: none;
                                                        padding: 10px 20px;
                                                        font-size: 16px;
                                                        border-radius: 5px;
                                                        cursor: pointer;
                                                        margin: 0 auto;
                                                    }
                                                    .download-button:hover {
                                                        background-color: #ff7f7f;
                                                    }
                                                    </style>
                                                    """,
                                                    unsafe_allow_html=True
                                                )

                                                st.download_button(
                                                    label="Download",
                                                    data=media_bytes,
                                                    file_name=filename,
                                                    mime=f"image/{media_types[index]}" if media_types[
                                                                                              index] == 'jpg' else f"video/{media_types[index]}",
                                                    key=f"download_button_{index}",
                                                    help="Download this media file"
                                                )

                                                # Apply the CSS class to the download button
                                                st.markdown(
                                                    f"""
                                                    <script>
                                                    var button = document.querySelector('button[aria-describedby="download_button_{index}"]');
                                                    button.classList.add('download-button');
                                                    </script>
                                                    """,
                                                    unsafe_allow_html=True
                                                )
                                            else:
                                                st.error(f"Failed to download media {index + 1}.")

                            st.markdown('</div>', unsafe_allow_html=True)
                            st.session_state.counter += 1
                        else:
                            st.error("Could not extract media from the provided URL. Please Try Again with Correct URL")
                except:
                    st.error("Please Try Again")
                    pass


    elif selected == "Terms & Conditions":
        # Add your terms and conditions here
        st.write("Terms and Conditions")
    elif selected == "Privacy Policy":
        # Add your privacy policy here
        st.write("Privacy Policy")
    elif selected == "About":
        # Add information about your app here
        st.write("About")


if __name__ == "__main__":
    main()
