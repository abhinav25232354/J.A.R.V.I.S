def todo_list():
    try:
        '''Todo List Takes no parameter'''
        print("1. Add\n2. Remove\n3. ListOut\n4. Empty")
        user = int(input("--> "))
        if user==1:
            f = open("Todo.txt", "a")
            text = input("Text: ")
            f.write(f"{text}\n")
            f.close()
        elif user==2:
        # Open file in read mode to get lines
            with open("Todo.txt", "r") as f:
                lines = f.readlines()
                index_to_remove = int(input("Index Starts from 0 (Which line to remove): "))
            if 0 <= index_to_remove < len(lines):
                del lines[index_to_remove]
            else:
                print("Invalid index")
                exit()

            # Rewrite file with updated lines
            with open("Todo.txt", "w+") as f:
                f.writelines(lines)
                f.read()

        elif user==3:
            f = open("Todo.txt", "r+")
            if f.read() == "":
                print("No Items in Todo List")
                f.close()
            else:
                f.seek(0)
                print(f.read())
                f.close()
        elif user==4:
            f = open("Todo.txt", "w")
            f.write("")
            f.close()
    except Exception as e:
        print(e)

def note():
    try:
        f = open("Notes.txt", "a+")
        print("1. Read\n2. Write")
        user = int(input("--> "))
        match(user):
            case 1:
                if f.read() == "":
                    f.seek(0)
                    print("Nothing to Show in Notes")
                    f.close()
                else:
                    f.seek(0)
                    f.read()
                    f.close()
            case 2:
                text = input("Text: ")
                f.seek(0)
                f.write(f"{text}\n")
                f.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # todo_list()
    note()