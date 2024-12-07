import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer

# Lade das Modell und den Tokenizer
MODEL_NAME = "Salesforce/codegen-2B-multi"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)


def generate_response(prompt):
    """Generiert eine Antwort basierend auf dem Prompt"""
    # Tokenisiere die Eingabe
    input_ids = tokenizer.encode(prompt, return_tensors="pt")

    # Generiere Antwort
    output = model.generate(
        input_ids,
        max_length=1000,  # Maximale Länge der Antwort
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id,
        do_sample=True,
    )

    # Dekodiere die Antwort und gebe sie aus
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    return response


def main():
    """Hauptfunktion, um über Kommandozeile Eingaben entgegenzunehmen"""
    parser = argparse.ArgumentParser(description="Interagiere mit dem CodeGen-2B-Multi Modell")
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="Dein Eingabetext oder Frage für das Modell",
    )

    args = parser.parse_args()

    if args.query:
        # Antwort generieren
        response = generate_response(args.query)
        print("\nAntwort vom Modell:")
        print(response)
    else:
        # Wenn keine Eingabe gemacht wurde, interaktiven Modus starten
        print("Starte interaktiven Modus. Gib 'exit' ein, um das Programm zu beenden.")
        while True:
            user_input = input("\nDeine Eingabe: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Beende das Modell...")
                break
            response = generate_response(user_input)
            print("\nAntwort vom Modell:")
            print(response)


if __name__ == "__main__":
    main()
