import os
from dotenv import load_dotenv
from google import genai

# 1. Cargamos las variables secretas del archivo .env
load_dotenv()

# 2. Leemos la API Key desde el entorno del sistema
api_key = os.getenv("GEMINI_API_KEY")

# 3. Inicializamos el cliente oficial de Gemini
client = genai.Client(api_key=api_key)

# 4. Enviamos una prueba simple al modelo
respuesta = client.models.generate_content(
    model='gemini-3.8-flash',
    contents='Responde con una sola frase: ¿Estás listo para trabajar con SQL?'
)

print("=== RESPUESTA DE GEMINI ===")
print(respuesta.text)