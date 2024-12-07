from django.shortcuts import render
from django.http import JsonResponse
from transformers import AutoModelForCausalLM, AutoTokenizer
from threading import Lock


# Neues Modell: CodeGen-2B
model_name = "EleutherAI/gpt-neo-1.3B"


class ModelSingleton:
    """
    Singleton-Pattern mit Cache und Lazy Loading.
    """
    _model = None
    _tokenizer = None
    _lock = Lock()  # Thread-Safe Singleton Initialisierung

    @classmethod
    def get_model(cls):
        # Sicherstellen, dass das Modell nur einmal geladen wird
        with cls._lock:  # Sperren, um Threading-Probleme zu vermeiden
            if cls._model is None:
                cls._tokenizer = AutoTokenizer.from_pretrained(model_name)
                cls._model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="cpu"
                )
        return cls._model, cls._tokenizer


def load_chat_view(request):
    # Lade das Template für Chatbot
    return render(request, 'chatbot/chat.html')


def chatbot_response(request):
    user_input = request.GET.get('query', '')

    if not user_input:
        return JsonResponse({"response": "Bitte geben Sie eine Frage ein."})

    # Lazy Loading mit Singleton und sicherstellen, dass nur einmal geladen wird
    model, tokenizer = ModelSingleton.get_model()

    # Tokenisieren und KI-Response generieren
    inputs = tokenizer.encode(user_input, return_tensors="pt")
    outputs = model.generate(inputs, max_length=700, num_return_sequences=1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Antwort als JSON zurückgeben
    return JsonResponse({"response": response})
