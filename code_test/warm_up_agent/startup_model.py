import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

if torch.cuda.is_available():
    model = model.cuda()

while True:
    user_input = input("Você: ")
    if user_input.lower() in ['quit', 'sair']:
        break
    
    inputs = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors='pt')
    if torch.cuda.is_available():
        inputs = inputs.cuda()
    
    with torch.no_grad():
        outputs = model.generate(inputs, max_length=inputs.shape[1] + 100, pad_token_id=tokenizer.eos_token_id)
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = response[len(user_input):].strip()
    
    print(f"Bot: {response}")