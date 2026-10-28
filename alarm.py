import datetime
from playsound import playsound

def ring_alarm(hour, minute):
    try:
        h = datetime.datetime.now().hour
        m = datetime.datetime.now().minute
        if h==hour and m==minute:
            print(f"Alarm: {h}{minute}")
            # playsound('alarm.mp3')
        else:
            print("Unable to toggle Alarm! Sorry")
    except Exception as e:
        print(e)

def reminder(thing, hour, minute):
    try:
        # hour = int(input("Hour: "))
        # minute = int(input("Minute: "))
        h = datetime.datetime.now().hour
        m = datetime.datetime.now().minute
        if h==hour and m==minute:
            print(f"Reminder:\n{thing}")
    except Exception as e:
        print(e)