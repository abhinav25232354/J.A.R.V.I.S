import asyncio
import edge_tts
from playsound import playsound

async def speech(audio):
    try:
        text = audio
        # communicate = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
        # communicate = edge_tts.Communicate(text=text, voice="ur-PK-AsadNeural")
        # communicate = edge_tts.Communicate(text=text, voice="ur-PK-UzmaNeural")
        communicate = edge_tts.Communicate(text=text, voice="en-US-AndrewMultilingualNeural")
        # communicate = edge_tts.Communicate(text=text, voice="en-US-AvaMultilingualNeural")
        # communicate = edge_tts.Communicate(text=text, voice="en-US-BrianMultilingualNeural")
        # communicate = edge_tts.Communicate(text=text, voice="en-US-EmmaMultilingualNeural")
        # communicate = edge_tts.Communicate(text=text, voice="en-US-AriaNeural")
        # communicate = edge_tts.Communicate(text=text, voice="en-US-ChristopherNeural")
        # communicate = edge_tts.Communicate(text=text, voice="en-US-JennyNeural")
        # communicate = edge_tts.Communicate(text=text, voice="en-IN-NeerjaNeural")
        # communicate = edge_tts.Communicate(text=text, voice="en-US-GuyNeural")
        # communicate = edge_tts.Communicate(text=text, voice="en-GB-RyanNeural", rate="+2%")
        # communicate = edge_tts.Communicate(text=text, voice="en-IN-PrabhatNeural", rate="+35%", pitch="+10%")
        # communicate = edge_tts.Communicate(text=text, voice="hi-IN-SwaraNeural")
        # communicate = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
        await communicate.save("output.mp3")  # Saves the output as MP3
    except Exception as e:
        print(e)
    # finally:
        # print("Executed Successfully")

# from pydub import AudioSegment

# def speed_up_audio(file_path, speed=1.5, output_file="faster_audio.mp3"):
#     audio = AudioSegment.from_file(file_path)
#     faster_audio = audio.speedup(playback_speed=speed)
#     faster_audio.export(output_file, format="mp3")
#     print(f"Saved faster audio to: {output_file}")

# # Example usage
# speed_up_audio("output.mp3", speed=2.0)


if __name__ == "__main__":
    asyncio.run(speech("Hello Sir, I am Jarvis, tell me how can i help you, Sir system condition is going critical, should i do something"))
    # asyncio.run(speech(""""""))
    playsound("output.mp3")