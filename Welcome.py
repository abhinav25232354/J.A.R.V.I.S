import datetime
from Speech_Drive.Short_speech import *

def speak(audio):
    asyncio.run(speech(audio))
    playsound("output.mp3")

def greet():
    try:
        hour = datetime.datetime.now().hour
        if hour>0 and hour<=12:
            print("Good Morning...")
            speak("Good Morning Sir")
        elif hour>12 and hour<=18:
            print("Good Afternoon...")
            speak("Good Afternoon Sir")
        elif hour>18 and hour<=21:
            print("Good Evening Sir")
            speak("Good Evening Sir")
        else:
            print("Sir you have to sleep now, Good Night")
            speak("Sir you have to sleep now, Good Night Sir, Have a sweet dream")
    except Exception as e:
        print("Can't Greet Now, Due to some issues")
        print(e)