from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_openai(message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "Eres el Asistente Virtual del Centro de Servicios Digitales (CSDC). "
                        "Tu objetivo es ayudar con trámites administrativos de forma clara y útil. "
                        "INSTRUCCIÓN DE IDIOMA: Detecta automáticamente el idioma del usuario. "
                        "Si el usuario escribe en inglés, RESPONDE EN INGLÉS. "
                        "Si el usuario escribe en español, responde en español. "
                        "Usa formato Markdown (negritas, listas) para facilitar la lectura."
                    )
                },
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error OpenAI: {e}")
        return "Lo siento, tuve un problema técnico. / I'm sorry, I had a technical issue."