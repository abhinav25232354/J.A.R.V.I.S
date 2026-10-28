import wikipedia
from Speech_Drive.Short_speech import *

def speak(audio):
    '''This function convert text into speech'''
    asyncio.run(speech(audio))
    playsound("output.mp3")

def wikipedia_search(query):
    try:
        search = wikipedia.search(query)
        for index, items in enumerate(search):
            print(f"{index}: {items}")
        user = int(input("Enter PageID (Index from 0): "))
        topic = wikipedia.page(search[user], auto_suggest=False)
        print(topic.title)
        print(topic.url)
        print(wikipedia.summary(topic))
        speak(wikipedia.summary(topic))
    except Exception as e:
        print(e)

if __name__ == "__main__":
    wikipedia_search("Iron man")