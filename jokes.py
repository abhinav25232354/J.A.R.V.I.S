import requests
from Speech_Drive.Short_speech import *

# Speak Function
def speak(audio):
    '''This function convert text into speech'''
    asyncio.run(speech(audio))
    playsound("output.mp3")

def get_random_joke():
    try:
        url = "https://official-joke-api.appspot.com/jokes/random"
    
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for bad responses

            joke = response.json()
            setup = joke.get("setup")
            punchline = joke.get("punchline")

            print(f"😂 Sir, Here's a joke for you:\n\n{setup}\n{punchline}")
            speak(f"😂 Sir, Here's a joke for you:\n\n{setup}\n{punchline}")

        except requests.exceptions.RequestException as e:
            print(f"Oops! Couldn't fetch a joke. Error: {e}")
            # speak(f"Oops! Couldn't fetch a joke. Error: {e}")
    except Exception as e:
        print(e)

# Example usage
if __name__ == "__main__":
    print(get_random_joke())
