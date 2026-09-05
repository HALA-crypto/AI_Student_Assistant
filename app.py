import streamlit as st
import io
import asyncio
import tempfile
import os
import numpy as np
from PIL import Image, ImageFilter
from deep_translator import GoogleTranslator
import edge_tts
import PyPDF2
import json
import re
import subprocess
from groq import Groq
st.title("AI Student Assistant 🤖")
st.write("Your smart assistant for studying, translating, summarizing and more!")
st.markdown("---")
st.sidebar.title("📚Your Tools")
tools = st.sidebar.radio("Select your tool:", ["🤖 AI Assistant", "🌍Translator", "📃PDF Summarizer", "🎙️Text To Speech", "📄Extract Text From Audio or Video", "🖼️Image Filter"])
if tools == "🤖 AI Assistant":
    st.subheader("🤖 AI Assistant")
    st.write("Ask me anything and I'll do my best to help you!")
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    st.markdown("---")
    audio_input = st.audio_input("Record your message:")
    chat_input = st.chat_input("Or type your message:")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    if chat_input:
        st.session_state.messages.append({"role": "user", "content": chat_input})
        with st.chat_message("user"):
            st.write(chat_input)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    messages = [{"role":"system", "content": "You are a helpful assistant."}]
                    for msg in st.session_state.messages:
                        messages.append({"role":msg["role"], "content": msg["content"]})
                    response = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=messages,
                        max_tokens=500,
                        temperature=0.7,
                    ) 
                    answer = response.choices[0].message.content
                except Exception as e:
                    answer = e 
            st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
    if audio_input:
        if st.button("Send"):
            with st.spinner("Converting to text..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav")as temp:
                    temp.write(audio_input.read())
                    path=temp.name 
                try:
                    with open(path, "rb") as f:
                        transcript=client.audio.transcriptions.create(
                            model="whisper-large-v3",
                            file=(os.path.basename(path), f),
                            response_format="text"
                        )
                finally:
                    os.unlink(path)
            if not transcript or len(transcript)<2:
                st.error("Try again")
            else:
                st.session_state.messages.append({"role":"user","content":transcript})
                with st.chat_message("user"):
                    st.write(f"{transcript}")
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            messages = [{"role":"system", "content":"You are a helpful assistant."}]
                            for msg in st.session_state.messages:
                                messages.append({"role":msg["role"], "content":msg["content"]})
                            response = client.chat.completions.create(
                                model="openai/gpt-oss-120b",
                                messages=messages,
                                max_tokens=500,
                                temperature=0.7,
                            )
                            answer = response.choices[0].message.content
                        except Exception as e:
                            answer = e
                    st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
elif tools == "🌍Translator":
    st.subheader("🌍Translator")
    st.write("Translate text between different languages easily!")
    language={
        "English": "en",
        "Arabic": "ar",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Russian": "ru",
        "Chinese": "zh-CN",
        "Japanese": "ja",
        "Korean": "ko"
    }
    col1, col2 = st.columns(2)
    with col1:
        Source_language = st.selectbox("Select source language", list(language.keys()), index=0)
    with col2:
        Target_language = st.selectbox("Select target language", list(language.keys()), index=1)
    text_input = st.text_area("Enter your text to translate", height=100, placeholder="Type your text here...")
    if st.button("Translate", use_container_width=True):
        if text_input == "":
            st.warning("Please enter text to translate.")
        else:
            try:
                translated_text = GoogleTranslator(source=language[Source_language], target=language[Target_language]).translate(text_input)
                st.text_area("Your Translated Text", value=translated_text, height=100)
            except:
                st.error("An error occurred during translation. Please try again.")
elif tools == "📃PDF Summarizer":
    st.subheader("📃PDF Summarizer")
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    st.write("Upload a PDF file or paste your text to get a summary in 3 simple sentences!")
    file = st.file_uploader("Upload your text file", type=["pdf"])
    if file is not None:
        pdf_reader= PyPDF2.PdfReader(io.BytesIO(file.read()))
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text() or ""
        if pdf_text.strip():
            st.info(f"Text extracted from the uploaded PDF: {len(pdf_reader.pages)} pages")
            text_from_pdf = pdf_text
        else:
            st.warning("No text found in the uploaded PDF.")
            text_from_pdf = ""
    else:
        text_from_pdf = ""
    text = st.text_area("Or paste your text here:", height=200 , value=text_from_pdf)
    if st.button("Summarize"):
        if len(text.strip()) < 10:
            st.warning("Please enter at least 10 characters of text to summarize.")
        else:
            with st.spinner("Generating summary..."):
                arabic_letters = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
                lang = "Arabic" if arabic_letters > 10 else "English"
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": f"you are a helpful assistant, summarize the text into 3 simple sentences, in {lang} language."},
                        {"role": "user", "content": text}
                    ]
                )
                st.success(response.choices[0].message.content)
elif tools == "🎙️Text To Speech":
    st.subheader("Convert Text to Speech")
    st.write("Enter text and select a voice to generate speech from your text!")
    text=st.text_area("Enter text to convert to speech")
    language=st.selectbox("Select language",["عربي","English"])
    VOICES = {
        "عربي": {
            
            " زارية (امرأة - السعودية)": "ar-SA-ZariyahNeural",
            " فهد (رجل - السعودية)":     "ar-SA-FahdNeural",
            " محمد (رجل - مصر)":         "ar-EG-ShakirNeural",
            " سلمى (امرأة - مصر)":       "ar-EG-SalmaNeural",
        },
        "English": {
            " Jack (Male - USA)":       "en-US-GuyNeural",
            " Jenny (Female - USA)":    "en-US-JennyNeural",
            " Ryan (Male - UK)":   "en-GB-RyanNeural",
            " Lily (Female - UK)": "en-GB-LibbyNeural",
        },
    }
    voice=st.selectbox("Select voice",list(VOICES[language].keys()))
    voice_id=VOICES[language][voice]
    async def generate_audio(text, voice):
        communicate = edge_tts.Communicate(text=text, voice=voice)
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        return b"".join(audio_chunks) 
    if st.button("Generate Audio"):
        if text:
            audio_bytes = asyncio.run(generate_audio(text, voice_id))
            st.audio(audio_bytes, format="audio/mp3")
        else:
            st.warning("Please enter some text to convert to speech.")
elif tools == "📄Extract Text From Audio or Video":
    st.title("Extract Text from Audio or Video")
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    st.subheader("Upload your audio or video file")
    uploaded = st.file_uploader("Upload your file", type=["mp4", "mp3", "wav", "m4a", "ogg", "webm"])
    def transcribe_audio_file(path):
        with open(path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=(os.path.basename(path), f),
                response_format="text"
            )
        return transcript    
    if uploaded:
        if uploaded.size / 1024**2 > 25:
            st.error("File size exceeds 25MB limit. Please upload a smaller file.")
        elif st.button("Extract Text", key="file_btn"):
            with st.spinner("Extracting text from audio/video..."):
                ext = os.path.splitext(uploaded.name)[-1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                    tmp_file.write(uploaded.read())
                    path = tmp_file.name
                try:
                    transcript = transcribe_audio_file(path)
                finally:
                    os.unlink(path)    
            if not transcript or len(transcript.strip()) < 5:
                st.error("Could not extract text from the audio/video.")
            else:
                st.subheader("The Extracted Text:")
                st.write(transcript)
                st.download_button("Download Transcript", transcript, file_name="transcript.txt")
    def parse_json3_sub(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            lines = []
            for event in data.get("events", []):
                for segment in event.get("segs", []):
                    word = segment.get("utf8", "").strip()
                    if word and word != "\n":
                        lines.append(word)
            full_text = " ".join(lines)
            return re.sub(r"\s+", " ", full_text).strip()
    def get_yt_transcript(url):
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "subs")
        for lang in ["en", "ar", ""]:
            cmd = [
                "yt-dlp", "--no-playlist", "--skip-download",
                "--write-subs", "--write-auto-subs",
                "--sub-format", "json3",
                "-o", output_path,
            ]
            if lang :
                cmd += ["--sub-langs", lang]
            cmd.append(url)
            subprocess.run(cmd, capture_output=True, text=True)
            for f in os.listdir(temp_dir):
                if f.endswith(".json3"):
                    sub_path = os.path.join(temp_dir, f)
                    text = parse_json3_sub(sub_path)
                    for file in os.listdir(temp_dir):
                        try:
                            os.unlink(os.path.join(temp_dir, file)) 
                        except:
                            pass
                    if text.strip():
                        return text
        raise ValueError("No subtitles found for the provided YouTube link.")
    st.markdown("---")
    st.subheader("Upload your YouTube video link")
    youtube_link = st.text_input("Enter YouTube video link", placeholder="https://www.youtube.com/watch?v=...")
    if youtube_link:
        if "youtube.com" not in youtube_link and "youtu.be" not in youtube_link:
            st.error("Please enter a valid YouTube link.")
        elif st.button("Extract Text", key="yt_btn"):
                try:
                    with st.spinner("Extracting text from YouTube video..."):
                        transcript = get_yt_transcript(youtube_link)
                    st.subheader("The Extracted Text:")
                    st.write(transcript)
                    st.download_button("Download Transcript", transcript, file_name="transcript.txt")
                except:
                    st.error("Error extracting text from your YouTube video.")
                    transcript = None
elif tools == "🖼️Image Filter":
    st.subheader("🖼️Image Filter")
    st.write("Upload an image and apply different filters to enhance it!")
    def Filter_Vintage(img):
        arr = np.array(img, dtype=np.float32)
        arr [:,:,0] = np.clip(arr [:,:,0]*1.1+20, 0, 255)
        arr [:,:,1] = np.clip(arr [:,:,1]*0.9+10, 0, 255)
        arr [:,:,2] = np.clip(arr [:,:,2]*0.75, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))
    def Filter_BlackWhite(img):
        return img.convert("L").convert("RGB")
    def Filter_sharpe(img):
        return img.filter(ImageFilter.SHARPEN)
    def Filter_Warm(img):
        arr = np.array(img, dtype=np.float32)
        arr [:,:,0] = np.clip(arr [:,:,0]+40, 0, 225)
        arr [:,:,2] = np.clip(arr [:,:,2]-40, 0, 225)
        return Image.fromarray(arr.astype(np.uint8))
    def Filter_Cinema(img):
        arr = np.array(img, dtype=np.float32)
        arr [:,:,0] = np.clip(arr [:,:,0]*0.9, 0, 225)
        arr [:,:,2] = np.clip(arr [:,:,2]*1.2, 0, 225)
        return Image.fromarray(arr.astype(np.uint8))

    Filters = {
        "None" : None,
        "Vintage": Filter_Vintage,
        "Black & White": Filter_BlackWhite,
        "Warm": Filter_Warm,
        "Cinema": Filter_Cinema,
        "Sharpen": Filter_sharpe
    }
    image_file = st.file_uploader("Upload your image", type=["jpg", "jpeg", "png"])
    if image_file:
        img = Image.open(image_file).convert("RGBA")
        st.image(img, caption="Your Uploaded Image")
        st.subheader("Select Your Filter")
        choice = st.radio("", list(Filters.keys()),horizontal=True)
        filtered = img.convert("RGB")
        if Filters[choice]:
            filtered = Filters[choice](filtered)
        st.subheader("Your Filtered Image")   
        st.image(filtered)
        byte_data = io.BytesIO()
        filtered.save(byte_data, format="PNG")
        byte_data = byte_data.getvalue()
        st.download_button("Download Filtered Image", data=byte_data, file_name="filtered_image.png", mime="image/png")
                
