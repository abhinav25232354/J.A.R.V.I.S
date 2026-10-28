import datetime
from Speech_Drive.Short_speech import *

def speak(audio):
    asyncio.run(speech(audio))
    playsound("output.mp3")

def get_time():
    try:
        time = datetime.datetime.now().hour
        # print(time)
        if time>=12 and time<=15:
            print("I think you should take rest for some time, and you can continue your work after 3 PM")
            speak("I think you should take rest for some time, and you can continue your work after 3 PM")
        elif time>=15 and time<=17:
            print("Sir, its time for your coffee")
            speak("Sir, its time for your coffee")
        elif time>=17:
            print("Sir, you should shut down now, it is not good for your health")
            speak("Sir, you should shut down now, it is not good for your health")
        print(datetime.datetime.now())
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    get_time()