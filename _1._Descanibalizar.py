import spacy
import pandas as pd
from scipy.spatial.distance import cdist
from nltk.corpus import stopwords

# Cargar el modelo de procesamiento de lenguaje natural de spaCy para el español
modelo_nlp = spacy.load('es_core_news_lg')

# Cargar la lista de palabras de parada en español
palabras_de_parada = set(stopwords.words('spanish'))

# Definir la ruta del archivo de texto
ruta_archivo = "2._Keywords.txt"

# Abrir el archivo en modo lectura y leer todas las líneas
with open(ruta_archivo, "r", encoding="utf-8") as archivo:
    lineas = archivo.readlines()

# Imprimir el número de líneas iniciales en el archivo
print(f"Iniciales: {len(lineas)}")

# Crear un DataFrame de pandas con las líneas originales
df = pd.DataFrame(lineas, columns=['Original'])

# Procesar las líneas utilizando el modelo de spaCy
lineas_procesadas = list(modelo_nlp.pipe(df['Original'].str.strip()))

# Calcular las incrustaciones vectoriales de las líneas procesadas
incrustaciones = [doc.vector for doc in lineas_procesadas]

# Calcular la matriz de similitud de coseno entre las incrustaciones
matriz_similaridad = 1 - cdist(incrustaciones, incrustaciones, metric='cosine')

# Crear una lista de conjuntos para almacenar líneas similares
lineas_similares = [set() for _ in range(len(matriz_similaridad))]

# Comparar las líneas y construir el conjunto de líneas similares
for i in range(len(matriz_similaridad)):
    for j in range(i + 1, len(matriz_similaridad)):
        if matriz_similaridad[i, j] > 0.97:
            lineas_similares[i].add(j)
            lineas_similares[j].add(i)

# Crear un conjunto para almacenar las líneas a eliminar
lineas_a_eliminar = set()

# Identificar y marcar las líneas a eliminar
for i in range(len(matriz_similaridad)):
    if lineas_similares[i]:
        lineas_similares[i].add(i)
        linea_a_mantener = max(lineas_similares[i], key=lambda j: len(df.at[j, 'Original'].split()))
        lineas_a_eliminar.update(lineas_similares[i] - {linea_a_mantener})

# Filtrar el DataFrame para eliminar las líneas marcadas
df = df[~df.index.isin(lineas_a_eliminar)]

# Abrir el archivo en modo escritura y sobrescribir el contenido con las líneas filtradas
with open(ruta_archivo, "w", encoding="utf-8") as archivo:
    archivo.writelines(df['Original'])

# Imprimir el número de líneas eliminadas
print(f"Removidas: {len(lineas) - len(df)}")

# Imprimir el número de líneas finales en el archivo después del procesamiento
print(f"Finales: {len(df)}")
