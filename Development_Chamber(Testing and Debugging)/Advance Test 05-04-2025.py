# from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
# # Transformer made from the model from facebook, capable of answering and GPT, blenderbotTokenizer

# # Load the tokenizer and model
# # model_name = "facebook/blenderbot-9B" # Needs permission and API
# # model_name = "facebook/blenderbot-3B"
# model_name = "facebook/blenderbot-400M-distill" # blenderbot-400M-distill model preprocessing
# tokenizer = BlenderbotTokenizer.from_pretrained(model_name) # tokenizer for tokenizing strings
# model = BlenderbotForConditionalGeneration.from_pretrained(model_name) # Feeding model with pretrained transformer

# print("Jarvis: Hello! Ask me anything (type 'exit' to quit).")

# while True:
#     user_input = input("You: ")
#     if user_input.lower() in ['exit', 'quit', 'bye']:
#         print("Jarvis: Goodbye!")
#         break
    
#     # Read external knowledge
#     with open("knowledge_base.txt", "r", encoding="utf-8") as f:
#         knowledge = f.read()
#     # Combine knowledge + user question
#     contextual_input = f"{knowledge}\nUser: {user_input}"

#     inputs = tokenizer([contextual_input], return_tensors="pt", truncation=True, max_length=512)
#     # inputs = tokenizer([user_input], return_tensors="pt")
#     reply_ids = model.generate(**inputs)
#     response = tokenizer.batch_decode(reply_ids, skip_special_tokens=True)[0]

#     print("Jarvis:", response)


from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration

# Load model & tokenizer
model_name = "facebook/blenderbot-400M-distill"
tokenizer = BlenderbotTokenizer.from_pretrained(model_name)
model = BlenderbotForConditionalGeneration.from_pretrained(model_name)

# Load external knowledge
with open("knowledge_base.txt", "r", encoding="utf-8") as f:
    knowledge = f.read()

print("Jarvis: Hello! Ask me anything (type 'exit' to quit).")

while True:
    user_input = input("You: ")
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("Jarvis: Goodbye!")
        break

    # Combine knowledge and question
    prompt = f"{knowledge}\nUser: {user_input}"

    inputs = tokenizer([prompt], return_tensors="pt", truncation=True, max_length=512)
    reply_ids = model.generate(**inputs)
    response = tokenizer.batch_decode(reply_ids, skip_special_tokens=True)[0]

    print("Jarvis:", response)
