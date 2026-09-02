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
from groq import Groq
st.title("AI Student Assistant 🤖")
st.write("Your smart assistant for studying, translating, summarizing and more!")
st.markdown("---")
st.sidebar.title("📚Your Tools")
tools = st.sidebar.radio("Select your tool:", ["🤖 AI Assistant", "🌍Translator", "📃PDF Summarizer", "🎙️Text To Speech", "🖼️Image Filter"])
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
                