import time
import os
from main import handle_user_preference

executed_task = ""

# def execute(task):
#     handle_user_preference(task)
    # if task == "hello":
    #     print("Hello, User!")
    # elif task == "time":
    #     from datetime import datetime
    #     print("Current Time:", datetime.now().strftime("%H:%M:%S"))
    # elif task == "joke":
    #     print("Why don't scientists trust atoms? Because they make up everything!")
    # else:
    #     print(f"Unknown task: {task}")

while True:
    try:
        with open("task.txt", "r+") as f:
            content = f.read().strip()
            if content == "":
                pass
            else:
                # task = f.read()
                print(f"Command: {content}")
                handle_user_preference(content)
                print("Task Executed\n")
                f.seek(0) # Go back to the start of file
                f.truncate()  
                # f.close()
    except Exception as e:
        print(f"No Data: {e}")
        # if task and task != executed_task:
            # handle_user_preference(task)
            # executed_task = task
    # time.sleep(1)
