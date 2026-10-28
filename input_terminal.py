while True:
    task = input("Enter your task: ").strip()
    with open("task.txt", "w") as f:
        f.write(task)
