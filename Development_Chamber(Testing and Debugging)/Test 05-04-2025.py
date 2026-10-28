# import sys
# import sounddevice as sd
# import queue
# import json
# from vosk import Model, KaldiRecognizer

# # Load Vosk model
# model = Model(model_name="vosk-model-small-en-us-0.15")  # Fast & lightweight (~50MB)
# q = queue.Queue()

# # Callback to put microphone audio into a queue
# def callback(indata, frames, time, status):
#     if status:
#         print(status, file=sys.stderr)
#     q.put(bytes(indata))

# # Start listening and transcribing
# def recognize():
#     device = None  # Default input
#     samplerate = 16000  # Required by Vosk
#     with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=device,
#                            dtype='int16', channels=1, callback=callback):
#         print("🎙️ Say something (Press Ctrl+C to exit)...")
#         rec = KaldiRecognizer(model, samplerate)

#         while True:
#             data = q.get()
#             if rec.AcceptWaveform(data):
#                 result = json.loads(rec.Result())
#                 if result.get("text"):
#                     print("📝 You said:", result["text"])

# if __name__ == "__main__":
#     recognize()


import speech_recognition as sr

def recognize_speech():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎙️ Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)  # Optional: improves accuracy
        audio = recognizer.listen(source, phrase_time_limit=5)     # Listen for 5 seconds max

    try:
        print("🧠 Recognizing...")
        text = recognizer.recognize_google(audio)
        print("📝 You said:", text)
        return text
    except sr.UnknownValueError:
        print("❌ Could not understand the audio.")
    except sr.RequestError:
        print("⚠️ Request failed, check your internet.")

if __name__ == "__main__":
    while True:
        recognize_speech()
