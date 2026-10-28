import os
from Speech_Drive.Short_speech import *

def speak(audio):
    asyncio.run(speech(audio))
    playsound("output.mp3")

def garbage(folder_path):
    """
    Deletes all files in the specified folder, skipping those without delete permission.
    
    :param folder_path: Path to the folder whose files should be deleted.
    """
    try:
        if not os.path.exists(folder_path):
            print(f"Folder '{folder_path}' does not exist.")
            speak(f"Folder '{folder_path}' does not exist.")
            return
    
        if not os.path.isdir(folder_path):
            print(f"'{folder_path}' is not a directory.")
            speak(f"'{folder_path}' is not a directory.")
            return
    
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
        
            if os.path.isfile(file_path):  # Check if it's a file
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                    # speak(f"Deleted: {file_path}")
                except PermissionError:
                    print(f"Skipping (Permission Denied): {file_path}")
                    # speak(f"Skipping (Permission Denied): {file_path}")
            elif os.path.isdir(file_path):
                print(f"Skipping directory: {file_path}")
                # speak(f"Skipping directory: {file_path}")
        print("Garbage successfully Deleted, System Optimized")
        speak("Garbage Deleted Successfully, System Optimized")
    except Exception as e:
        print(e)

# Example usage:
if __name__ == "__main__":
    garbage("C:/Users/abhin/AppData/Local/Temp")