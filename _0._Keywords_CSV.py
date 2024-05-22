import os
import pandas as pd

# Obtener la ruta de la carpeta de keywords
ruta_carpeta_keywords = os.path.join(os.getcwd(), "_._Keywords_CSV")

# Inicializar una lista vacía para almacenar las keywords
keywords = []

# Iterar a través de los archivos en la carpeta
for archivo in os.listdir(ruta_carpeta_keywords):
    if archivo.endswith(".csv"):
        # Crear la ruta completa al archivo CSV
        ruta_archivo = os.path.join(ruta_carpeta_keywords, archivo)
        
        # Leer el archivo CSV en un DataFrame de pandas
        df = pd.read_csv(ruta_archivo)
        
        # Filtrar las keywords por posición y número de palabras
        keywords_en_archivo = df[df['Position'] <= 3]['Keyword'].tolist()
        keywords.extend([k for k in keywords_en_archivo if len(k.split()) >= 3])

# Definir la ruta del archivo de salida
ruta_archivo_salida = os.path.join(os.getcwd(), "2._Keywords.txt")

# Abrir el archivo de salida en modo escritura
with open(ruta_archivo_salida, "w", encoding="utf-8") as archivo_salida:
    # Escribir cada keyword en una línea separada en el archivo de salida
    for keyword in keywords:
        if keyword:  # Esto asegura que la keyword no esté vacía
            archivo_salida.write(keyword + "\n")

# Imprimir la cantidad total de keywords
print(f"Keywords: {len(keywords)}")
