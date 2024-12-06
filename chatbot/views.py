from django.shortcuts import render
from django.http import JsonResponse
from transformers import AutoModelForCausalLM, AutoTokenizer


class ModelSingleton:
    """
    Singleton-Pattern für Lazy Loading des Modells und Tokenizers.
    """
    _model = None
    _tokenizer = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")
            cls._model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-j-6B")
        return cls._model, cls._tokenizer


def load_chat_view(request):
    # Lade das Template, um den Chatbot anzuzeigen
    return render(request, 'chatbot/chat.html')


def chatbot_response(request):
    user_input = request.GET.get('query', '')

    if not user_input:
        return JsonResponse({"response": "Bitte geben Sie eine Frage ein."})

    # Lazy Loading und Singleton sicherstellen
    model, tokenizer = ModelSingleton.get_model()

    # Tokenisieren und KI-Response generieren
    inputs = tokenizer.encode(user_input, return_tensors="pt")
    outputs = model.generate(inputs, max_length=50, num_return_sequences=1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Antwort als JSON zurückgeben
    return JsonResponse({"response": response})
