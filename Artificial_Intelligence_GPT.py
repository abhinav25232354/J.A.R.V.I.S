from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration # BlenderBot AI Model
from Speech_Drive.Short_speech import * # Speech Drive Contains 

def speak(audio):
    asyncio.run(speech(audio))
    playsound("output.mp3")

def Go_For_Advance_AI_GPT(question):
    try:
        # Load model & tokenizer
        # model_name = "gpt2-xl"
        model_name = "facebook/blenderbot-400M-distill"
        # model_name = "facebook/blenderbot-1B"
        # model_name = "facebook/blenderbot-3B"
        # model_name = "facebook/blenderbot-11B"
        tokenizer = BlenderbotTokenizer.from_pretrained(model_name)
        model = BlenderbotForConditionalGeneration.from_pretrained(model_name)

        # Load external knowledge
        # with open("knowledge_base.txt", "r", encoding="utf-8") as f:
            # knowledge = f.read()

        # print("Jarvis: Hello! Ask me anything (type 'exit' to quit).")

        # while True:
        user_input = question
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Jarvis: Goodbye!")
            # break

        # Combine knowledge and question
        # prompt = f"{knowledge}\nUser: {user_input}"
        prompt = f"User: {user_input}"

        inputs = tokenizer([prompt], return_tensors="pt", truncation=True, max_length=512)
        reply_ids = model.generate(
            **inputs,
            max_length=200,       # Increase maximum tokens in the response
            min_length=30,        # Ensure a decent minimum response length
            length_penalty=1.0,   # Penalty for shorter sequences (1.0 = no penalty)
            num_beams=5,          # Beam search to improve response quality
            early_stopping=True
        )   # Stop early when optimal answer found)
        response = tokenizer.batch_decode(reply_ids, skip_special_tokens=True)[0]

        print("Blenderbot:", response)
        speak(response)
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    while True:
        user = input("--> ")
        Go_For_Advance_AI_GPT(user)