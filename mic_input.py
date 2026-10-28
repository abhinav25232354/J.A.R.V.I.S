import speech_recognition as sr

def recognize_speech():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)  # Optional: improves accuracy
        audio = recognizer.listen(source, phrase_time_limit=5)     # Listen for 5 seconds max

    try:
        print("Recognizing...")
        text = recognizer.recognize_google(audio)
        recognized_text = text
        print("You said:", text)
        return recognized_text
    except sr.UnknownValueError:
        print("Could not understand the audio.")
    except sr.RequestError:
        print("Request failed, check your internet.")
    return None

if __name__ == "__main__":
    while True:
        recognize_speech()