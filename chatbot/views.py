from django.shortcuts import render
from django.http import JsonResponse
from transformers import AutoModelForCausalLM, AutoTokenizer

# Funktion zum Laden des Modells
def load_model():
    model_name = "EleutherAI/gpt-j-6B"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    return model, tokenizer

# Initialisiere das Modell und den Tokenizer nur einmal
MODEL = None
TOKENIZER = None

def chatbot_response(request):
    global MODEL, TOKENIZER

    # Lade das Modell, falls es noch nicht geladen wurde
    if MODEL is None or TOKENIZER is None:
        MODEL, TOKENIZER = load_model()

    user_input = request.GET.get('query', '')  # Nutze die GET-Anfrage, um den Text zu erhalten
    if not user_input:
        return JsonResponse({"error": "No input provided"}, status=400)

    # Eingabe tokenisieren und Ausgabe generieren
    inputs = TOKENIZER.encode(user_input, return_tensors="pt")
    outputs = MODEL.generate(inputs, max_length=50, num_return_sequences=1)

    # Antwort dekodieren
    response = TOKENIZER.decode(outputs[0], skip_special_tokens=True)
    return JsonResponse({"response": response})
