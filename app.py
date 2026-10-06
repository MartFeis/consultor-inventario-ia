import streamlit as st
import pandas as pd
from motor_ia import obtener_esquema, generar_sql, ejecutar_consulta, generar_resumen


# Configuración básica de la página
st.set_page_config(page_title="Consultor de Inventario IA", layout="wide")

st.title("Consultor de Inventario IA")

st.write("Haz preguntas en lenguaje natural sobre la base de datos de inventario.")
st.sidebar.title("Tablas disponibles")
tabla_elegida=st.sidebar.selectbox("Selecciona una tabla:" , ["productos", "inventario_actual", "transacciones_stock"])
st.sidebar.dataframe(ejecutar_consulta(f'SELECT * FROM {tabla_elegida}'))

pregunta_usuario=st.text_input("Haz tu pregunta aquí: ")
if st.button("Generar Respuesta"):
    if pregunta_usuario== "":
        st.warning("Por favor ingresa una pregunta")
    else:
        esquema=obtener_esquema()
        sql=generar_sql(pregunta_usuario,esquema)
        st.write("SQL generado:")
        st.code(sql, language="sql")

        resultado=ejecutar_consulta(sql)

        if isinstance(resultado, pd.DataFrame):
            st.subheader("Resumen ejecutivo")
            st.write(generar_resumen(resultado,pregunta_usuario))
            st.subheader("tabla de resultado")
            st.dataframe(resultado)
        else:
            st.error(resultado)