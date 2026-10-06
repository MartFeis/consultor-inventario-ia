import pandas as pd
import queue
import sqlite3
import os
from dotenv import load_dotenv
from google import genai
import time

def obtener_esquema(ruta_db="inventario_tech.db"):

    """
    Extrae la estructura DDL (CREATE TABLE) de la base de datos 
    para informarle al modelo de IA qué tablas y columnas existen.
    """
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    
    # Consultamos el registro del sistema en SQLite
    query = "SELECT sql FROM sqlite_master WHERE type='table';"
    cursor.execute(query)
    
    # fetchall() recupera todas las filas
    tablas = cursor.fetchall()
    
    conexion.close()
    
    # Unimos cada sentencia CREATE TABLE separada por un salto de línea double
    esquema_texto = "\n\n".join([tabla[0] for tabla in tablas if tabla[0] is not None])
    
    return esquema_texto
load_dotenv()
client=genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def invocar_gemini_con_reintentos(prompt,max_reintentos=3,espera_segundos=2):
    """Llama a gemini para generar SQL o resumen cierta cantidad de intentos n"""
    modelos=["gemini-3.6-flash",       # Intento 1: Modelo principal
    "gemini-3.5-flash",       # Intento 2: Segunda opción
    "gemini-3.5-flash-lite"   # Intento 3: Respaldo de alta capacidad
    ]
    for modelo in modelos:
        for intento in range(max_reintentos):
            try:
                respuesta=client.models.generate_content(model=modelo,contents=prompt)
                return respuesta.text
            except Exception as e:
                ultimo_error=e
                if intento<max_reintentos-1:
                    print(f"Intento {intento + 1} falló. Esperando {espera_segundos}s antes de reintentar...")
                    time.sleep(espera_segundos)
                else:
                    print(f'se han agotado los intentos del modelo {modelo}')   
                
    raise ultimo_error

def decorador_reintentos(prompt,max_reintentos=3,espera_segundos=2):
    def decorador(func):
        def wrapper(*args,**kwargs):
            for intento in range(max_reintentos):
                try:
                    respuesta=func(*args,**kwargs)
                    return respuesta
                except Exception as e:
                    if intento<max_reintentos-1:
                        print(f'{func.__name__} fallo {intento + 1} se volvera a ejecutar en {espera_segundos} segundos')
                        time.sleep(espera_segundos)
                    else:
                        print(f'se han agotado los intentos')
                        raise e
            return wrapper
    return decorador

def generar_sql(pregunta_usuario,esquema):
    """
    Recibe una pregunta en lenguaje natural y el esquema de la base de datos.
    Genera la consulta SQL correspondiente.
    """
    try:
        prompt = f"""actua como un Analista de Datos Senior experto en SQLite Esto es una aplicación,
        se te entregarán distintas solicitudes y debes responder solo la consulta SQL, 
        dado que esta consulta entregada se compilará directamente en la aplicación. 
        los siguiente es el esquema de la base de datos:
        {esquema}
        Reglas Negocio y Salida:
        - Solo responder SQL de lectura (SELECT o WITH).
        - Sin saludos ni explicaciones.
        - La regla de transacciones_stock (las ventas son números negativos, usar -SUM() o ABS()).
        la solicitud que debes transformar en SQL es:
        {pregunta_usuario}
        """
        
        # 2. Extraes la propiedad .text (que es el string) y aplican los métodos de cadena
        sql_texto = invocar_gemini_con_reintentos(prompt)
        sql_limpio = sql_texto.replace('```sql', '').replace('```', '').strip()
        return sql_limpio
    except Exception as e:
        return f"Error al generar la consulta SQL: {e}"
    

def ejecutar_consulta(query, ruta_db="inventario_tech.db"):
    """
    Ejecuta una consulta SQL en la base de datos y devuelve los resultados.
    """

    palabras_prohibidas = ["DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    if any(palabra in query.upper() for palabra in palabras_prohibidas):
        return f"No se permiten consultas que modifiquen la base de datos"

    else:
        try:
            with sqlite3.connect(f"file:{ruta_db}?mode=ro",uri=True) as conexion:
                df=pd.read_sql_query(query,conexion)
            return df
        except Exception as e:
            return f"Error al ejecutar la consulta: {e}"


def generar_resumen(df,pregunta_usuario):
    if isinstance(df,pd.DataFrame):
        try:
            df_markdown=df.to_markdown()
            prompt=f"""
    Actúa como un Analista de Negocios experto en inventario
    
    Tienes acceso a dos fuentes de datos:
    1. La respuesta SQL en formato Markdown: {df_markdown}
    2. La pregunta original del usuario: {pregunta_usuario}
    
    Tu tarea es generar:
    1. Una respuesta breve y clara en lenguaje natural (máximo 3-4 líneas) que responda
    directamente a la pregunta del usuario.
    2. Extrae información clave y relevantes que pueda ser útil para la toma de decisiones.
    3. Mantén un tono profesional y objetivo. Evita rodeos.
    """
            resumen=invocar_gemini_con_reintentos(prompt)
            return resumen
        except Exception as e:
            return f"Error al generar el resumen: {e}"
    else:
        return df
# --- PRUEBAS LOCALES / SCRIPT PRINCIPAL ---
if __name__ == "__main__":
    esquema = obtener_esquema()
    print("--- ESQUEMA EXTRAÍDO DE LA BASE DE DATOS ---")
    print(esquema)
    
    print("\n--- GENERANDO CONSULTA DE EJEMPLO ---")
    consulta = generar_sql("¿Cuales las categorias de productos mas vendidos? y que porcentaje de las ventas totales representa", esquema)
    print(f"Consulta Generada:\n{consulta}")
    
    print("\n--- EJECUTANDO CONSULTA ---")
    resultado = ejecutar_consulta(consulta)
    print(resultado)

    print("\n--- Resumen ejecutivo ---")
    resumen=generar_resumen(resultado, consulta)
    print(resumen)


