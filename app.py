import streamlit as st
import os
import tempfile
from moviepy import VideoFileClip
import audio_utils
import captions
import time
from editing_engine import EditingEngine, EditingStep # Import both from editing_engine

# Remove the duplicate EditingStep enum definition from here

st.title("Captioning App")
st.write("Upload a video to automatically generate and add audio-synced captions.")

uploaded_file = st.file_uploader("Choose a video file...", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file is not None:
    # Create a temporary directory to save the uploaded file and outputs
        video_path = os.path.join(".", uploaded_file.name)
        audio_path = os.path.join(".", "extracted_audio.wav")
        output_video_path = os.path.join(".", "output_video.mp4")

        # Save the uploaded file
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File saved temporarily at {video_path}")

        # --- Processing Steps ---
        st.subheader("Processing Video...")

        # 1. Extract Audio and get video info
        progress_text = "Extracting audio and getting video info..."
        my_bar = st.progress(0, text=progress_text)
        try:
            video_clip = VideoFileClip(video_path)
            video_width, video_height = video_clip.size
            is_landscape = video_width / video_height > 1.0

            video_clip.audio.write_audiofile(audio_path, codec='pcm_s16le') # Use a common codec
            my_bar.progress(20, text=progress_text + " Done.")
            st.success("Audio extracted and video info obtained successfully.")
        except Exception as e:
            st.error(f"Error extracting audio or getting video info: {e}")
            st.stop()

        # 2. Perform Speech-to-Text
        progress_text = "Performing speech-to-text..."
        my_bar.progress(20, text=progress_text)
        try:
            # audio_utils.audioToText uses whisper-timestamped
            whisper_analysis = audio_utils.audioToText(audio_path)
            my_bar.progress(50, text=progress_text + " Done.")
            st.success("Speech-to-text analysis complete.")
        except Exception as e:
            st.error(f"Error during speech-to-text: {e}")
            st.stop()

        # 3. Generate Timed Captions
        progress_text = "Generating timed captions..."
        my_bar.progress(50, text=progress_text)
        try:
            # captions.getCaptionsWithTime formats the whisper output
            # Adjust maxCaptionSize based on landscape/portrait
            max_caption_size = 50 if is_landscape else 15
            timed_captions = captions.getCaptionsWithTime(whisper_analysis, maxCaptionSize=max_caption_size)
            my_bar.progress(70, text=progress_text + " Done.")
            st.success("Timed captions generated.")
            # Optionally display captions
            # st.write("Generated Captions:")
            # for (start, end), text in timed_captions:
            #     st.write(f"[{start:.2f}-{end:.2f}] {text}")
        except Exception as e:
            st.error(f"Error generating timed captions: {e}")
            st.stop()

        # 4. Prepare Editing Schema and Render
        progress_text = "Rendering video with captions..."
        my_bar.progress(70, text=progress_text)
        # The following block was moved inside the if uploaded_file is not None: block
        try:
            editing_engine = EditingEngine()
            # Add the original video as the background
            editing_engine.addEditingStep(EditingStep.ADD_BACKGROUND_VIDEO, {
                'url': video_path,
                'set_time_start': 0,
                'set_time_end': video_clip.duration
            })

            # Add the extracted audio
            editing_engine.addEditingStep(EditingStep.INSERT_AUDIO, {
                'url': audio_path,
                'set_time_start': 0,
                'set_time_end': video_clip.duration
            })

            # Determine which caption step to use based on aspect ratio
            caption_step=EditingStep.ADD_CAPTION_LANDSCAPE if is_landscape else EditingStep.ADD_CAPTION
            st.info(f"Using editing step: {caption_step.name} for captions.")

            # Add each timed caption as an editing step
            for (start_time, end_time), caption_text in timed_captions:
                # Ensure caption duration is not zero or negative
                if end_time > start_time:
                    editing_engine.addEditingStep(caption_step, {
                        'text': caption_text.upper(),  # Often captions are uppercase
                        'set_time_start': start_time,
                        'set_time_end': end_time
                    })
                else:
                    st.warning(f"Skipping caption with invalid timing: [{start_time:.2f}-{end_time:.2f}] {caption_text}")


            # Render the final video
            # The logger argument can be used to show progress from the rendering engine
            # For simplicity in Streamlit, we might omit or use a custom logger
            st.info("Rendering video... This might take a while.")
            editing_engine.renderVideo(output_video_path)

            my_bar.progress(100, text=progress_text + " Done.")
            st.success("Video rendered successfully!")

            # 5. Display the output video
            st.subheader("Output Video")
            st.video(output_video_path)

        except Exception as e:
            st.error(f"Error during video editing or rendering: {e}")
            st.exception(e)  # Display full traceback for debugging

