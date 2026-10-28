# Personal Modules
from Speech_Drive.Short_speech import * # It includes voice, ttsengine, modification
from garbage import garbage # Garbage function for optimizing system
from weather import get_weather # Weather function fetches realtime weather from weatherapi
from timeanddate import get_time # Used for recording time patches
from alarm import ring_alarm # Alarm rings on specific time provided by the user
from alarm import reminder # Reminder takes, thing, hour and minute as paramater
from wikipedia_search import wikipedia_search # search wikipedia for object takes single query parameter
from news import fetch_news # Takes query single parameter and returns summary of top 5 news of today
from jokes import get_random_joke # Takes no parameter
from todo import todo_list # Takes no parameter
from todo import note # Takes no parameter
from Welcome import greet # Takes no parameter
from internet_connectivity import get_network_report # Takes no argument
from Artificial_Intelligence_GPT import Go_For_Advance_AI_GPT # Handling general knowledge and conversations
from mic_input import recognize_speech # recognize speech with google cloud engine

# Python Libraries
import random # used for randomness in the program which is essential for AI Agent
import datetime
import time

hour = datetime.datetime.now().hour
minute = datetime.datetime.now().minute

# Speak Function
def speak(audio):
    '''This function convert text into speech'''
    asyncio.run(speech(audio))
    playsound("output.mp3")

# Global Variables - Will be used for Registering User for Jarvis
garbage_folder = "C:/Users/abhin/AppData/Local/Temp" # Garbage folder is just temporary folder which stores cache of programs to execute faster
weather_cities = ["Allahabad", "Kanpur", "Varanasi", "Lucknow"] # weather cities consist of cities on which it will randomly select one
random_weather_cities = random.choice(weather_cities)
reminder_text = "Its time to take a water break"
reminder_hour = 8
reminder_minute = 10
wikipedia_search_query = "Wikipedia"
news_topic = "Indian Government"
question = "Who is Elon Musk"

# Agentic Execution of tasks
task_list = [
    lambda: greet(), # Handled Exception
    lambda: get_time(), # Handled Exception
    lambda: speak(get_weather(random_weather_cities)), # Handled Exception
    lambda: garbage(garbage_folder), # Handled Exception
    lambda: ring_alarm(6, 51), # Handled Exception
    lambda: reminder(reminder_text, reminder_hour, reminder_minute), # Handled Exception
    lambda: wikipedia_search(wikipedia_search_query), # Handled Exception
    lambda: fetch_news(news_topic), # Handled Exception
    lambda: get_random_joke(), # Handled Exception
    lambda: todo_list(), # Handled Exception
    lambda: note(), # Handled Exception
    lambda: print(get_network_report()), # Handled Exception
    lambda: Go_For_Advance_AI_GPT(question), # Handled Exception
    lambda: recognize_speech() # Handled Exception
]

# while True:
    # selected_task = random.choice(task_list)  # Choose a function
    # selected_task()  # Execute the function
    # speak(command)
# fetch_news("Apple")
# get_weather("Allahabad")
# speak("Sir, the Mark VII is not ready for deployment. At this rate, you will burn through the arc reactor in less than 30 seconds. Might I suggest a more cautious approach? Or perhaps... call for backup? I must remind you, this is a high-risk engagement")
# print(weather.get_weather("Allahabad"))
# weather_report = weather.get_weather("Allahabad")
# speak(weather_report)

# speak("Good Morning sir! Would you like a weather update, news, or a reminder check?")
def handle_user_preference(command):
    if "greet" in command:
        greet()
    elif "clean" in command or "garbage" in command:
        garbage(garbage_folder)
    elif "weather" in command:
        get_weather(random_weather_cities)
    elif "time" in command:
        get_time()
    elif "alarm" in command:
        try:
            hour = int(input("Set alarm hour (24-hour format): "))
            minute = int(input("Set alarm minute: "))
            ring_alarm(hour, minute)
        except ValueError:
            speak("Invalid time format for alarm.")
    elif "remind" in command or "reminder" in command:
        try:
            reminder_text = input("What should I remind you about? ")
            reminder_hour = int(input("At what hour? (24-hour format): "))
            reminder_minute = int(input("At what minute? "))
            reminder(reminder_text, reminder_hour, reminder_minute)
        except ValueError:
            speak("Invalid input for reminder.")
    elif "wikipedia" in command:
        query = input("What should I search on Wikipedia? ")
        wikipedia_search(query)
    elif "news" in command:
        topic = input("Which topic should I get the news about? (Leave blank for general): ") or "Today's news"
        fetch_news(topic)
    elif "joke" in command:
        get_random_joke()
    elif "todo" in command:
        todo_list()
    elif "note" in command:
        note()
    elif "network" in command or "report" in command:
        print(get_network_report())
    else:
        Go_For_Advance_AI_GPT(command)
        # speak("Sorry, I didn't understand that. Say 'help' to know what I can do.")
        # print("Sorry, I didn't understand that. Say 'help' to know what I can do.")

# Smart Scheduling
def run_smart_schedule():
    try:
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute

        task_executed = False
        
        if hour == 6 and minute == 50:
            greet()
            task_executed = True
        elif hour == 6 and minute == 51:
            ring_alarm(6, 51)
            task_executed = True
        elif hour == 7 and minute == 0:
            speak(get_weather(random_weather_cities))
            task_executed = True
        elif hour == 7 and minute == 15:
            garbage(garbage_folder)
            task_executed = True
        elif hour == 8 and minute == 0:
            speak(fetch_news(news_topic))
            task_executed = True
        elif hour == 9 and minute == 0:
            speak(get_random_joke())
            task_executed = True
        elif hour == 9 and minute == 30:
            speak(wikipedia_search(wikipedia_search_query))
            task_executed = True
        elif hour == 10 and minute == 0:
            get_time()
            task_executed = True
        elif hour == 11 and minute == 0:
            reminder(reminder_text, reminder_hour, reminder_minute)
            task_executed = True
        elif hour == 12 and minute == 0:
            todo_list()
            task_executed = True
        elif hour == 13 and minute == 0:
            note()
            task_executed = True
        elif hour == 14 and minute == 0:
            print(get_network_report())
            task_executed = True
        else:
            print("Idle state no task scheduled at this time")  # Idle or no task scheduled at this time        
            # speak("Idle state Sir, no task scheduled at this time")  # Idle or no task scheduled at this time        
            print("Would you like a weather update, news, or a reminder check?")
            while True:
                command = input("--> ")
                handle_user_preference(command)
                break
    except Exception as e:
        print(e)

if __name__ == "__main__":
    while True:
        task = input("Enter your task: ").strip()
        # handle_user_preference(task)
        # task = recognize_speech()
        if task:
            print("Recognized:", task)
            with open("task.txt", "w") as f:
                f.write(task)
        else:
            print("No valid input recognized.")

            # f.close()
# run_smart_schedule()
#     while True:
#         time.sleep(5)
#         if run_smart_schedule():
#             # A scheduled task just ran. Skip to user interaction.
#             command = input("Now what can I help you with?\n> ").lower()
#             handle_user_preference(command)
#         else:
#             command = input("What can I do for you?\n> ").lower()
#             handle_user_preference(command)
#             # time.sleep(30)
#         # run_smart_schedule()