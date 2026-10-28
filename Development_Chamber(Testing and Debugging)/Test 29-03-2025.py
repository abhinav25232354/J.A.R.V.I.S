from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
model = AutoModelForCausalLM.from_pretrained("distilgpt2")

print("Jarvis: Hello! Ask me anything.")
while True:
    prompt = input("You: ")
    if prompt.lower() in ["exit", "quit"]:
        break

    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=50, do_sample=True)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("Jarvis:", response.replace(prompt, "").strip())
