import csv
import re
import concurrent.futures
import threading
import requests
import os
from unidecode import unidecode
from newspaper import Article
import slugify
import openai
from datetime import datetime

openai.api_key = "temp"

print("Inicio del script")

# Leer las API keys de archivos de texto
with open("0._ValueSERP.txt", "r", encoding="utf-8") as file:
    apis_valueserp = [line.strip() for line in file]
print("Leídas las API keys de ValueSERP")

with open("1._OpenAI.txt", "r", encoding="utf-8") as file:
    apis_openai = [line.strip() for line in file]
print("Leídas las API keys de OpenAI")

with open("2._Keywords.txt", "r", encoding="utf-8") as file:
    keywords = [line.strip() for line in file]
print("Leídas las keywords")

# Función para cargar el contenido de un archivo
def load_component(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read().strip()

# Cargar componentes de conversación y contenido
print("Cargando componentes de conversación y contenido")
pregunta_sistema = load_component("0._Sistema/0._Pregunta.txt")
pregunta_usuario = load_component("1._Usuario/0._Pregunta.txt")
pregunta_asistente = load_component("2._Asistente/0._Pregunta.txt")

titulo_sistema = load_component("0._Sistema/1._Titulo.txt")
titulo_usuario = load_component("1._Usuario/1._Titulo.txt")
titulo_asistente = load_component("2._Asistente/1._Titulo.txt")

investigacion_sistema = load_component("0._Sistema/2._Investigacion.txt")
investigacion_usuario = load_component("1._Usuario/2._Investigacion.txt")
investigacion_asistente = load_component("2._Asistente/2._Investigacion.txt")

estructura_sistema = load_component("0._Sistema/3._Estructura.txt")
estructura_usuario = load_component("1._Usuario/3._Estructura.txt")
estructura_asistente = load_component("2._Asistente/3._Estructura.txt")

articulo_sistema = load_component("0._Sistema/4._Articulo.txt")
articulo_usuario = load_component("1._Usuario/4._Articulo.txt")
articulo_asistente = load_component("2._Asistente/4._Articulo.txt")

descripcion_sistema = load_component("0._Sistema/5._Descripcion.txt")
descripcion_usuario = load_component("1._Usuario/5._Descripcion.txt")
descripcion_asistente = load_component("2._Asistente/5._Descripcion.txt")

imagen_sistema = load_component("0._Sistema/6._Imagen.txt")
imagen_usuario = load_component("1._Usuario/6._Imagen.txt")
imagen_asistente = load_component("2._Asistente/6._Imagen.txt")

categoria_sistema = load_component("0._Sistema/7._Categoria.txt")
categoria_usuario = load_component("1._Usuario/7._Categoria.txt")
categoria_asistente = load_component("2._Asistente/7._Categoria.txt")

print("Componentes de conversación y contenido cargados")

# Variables globales
total_keywords = len(keywords)
api_valueserp_actual = 0
api_openai_actual = 0
contador_keywords = 0

# Función para obtener resultados de ValueSERP
def obtenerValueSERP(keyword):
    global api_valueserp_actual
    print(f"Obteniendo resultados de ValueSERP para la keyword: {keyword}")
    while True:
        apiKey = apis_valueserp[api_valueserp_actual]
        parametros = {
            'api_key': apiKey,
            'q': keyword,
            'gl': "mx",
            'hl': "es"
        }
        url = 'https://api.valueserp.com/search'
        try:
            response = requests.get(url, params=parametros, timeout=60)
            response_json = response.json()
            resultado = response_json.get('organic_results', [])
            print(f"Resultados obtenidos de ValueSERP para {keyword}: {resultado}")
            return resultado
        except Exception as e:
            print(f"Error en obtenerValueSERP: {e}")
            api_valueserp_actual = (api_valueserp_actual + 1) % len(apis_valueserp)

# Función para descargar y analizar un artículo
def descargar_articulo(articulo):
    try:
        articulo.download()
        articulo.parse()
        print("Artículo descargado y analizado")
    except Exception as e:
        print(f"Error en descargar_articulo: {e}")

# Función para realizar una conversación con OpenAI
def chatGPT(sistema, usuario, asistente):
    global api_openai_actual
    print("Iniciando conversación con OpenAI")
    while True:
        api_openai_actual = (api_openai_actual + 1) % len(apis_openai)
        openai.api_key = apis_openai[api_openai_actual]
        try:
            respuesta = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": usuario},
                    {"role": "assistant", "content": asistente}
                ],
                temperature=0.1
            )
            # Imprimir la respuesta completa para depuración
            print("Respuesta completa de la API:", respuesta)
            
            # Acceder al contenido de la respuesta
            content = respuesta.choices[0].message.content
            content_strip = content.strip()
            print("Conversación con OpenAI completada")
            print("Contenido recibido:", content_strip)
            return content_strip
        except openai.error.OpenAIError as e:
            print(f"Error en chatGPT: {e}")
            pass

# Función para crear una pregunta
def crear_pregunta(keyword, titulos):
    print(f"Creando pregunta para la keyword: {keyword}")
    return chatGPT(pregunta_sistema.format(keyword=keyword), pregunta_usuario.format(titulos=titulos), pregunta_asistente)

# Función para crear un título
def crear_titulo(pregunta, keyword, titulos):
    print(f"Creando título para la pregunta: {pregunta}")
    titulo = chatGPT(titulo_sistema.format(pregunta=pregunta, keyword=keyword), titulo_usuario.format(titulos=titulos), titulo_asistente)
    titulo = titulo.replace("\"", "").rstrip(".")
    intentos = 0
    while len(titulo) > 70 and intentos < 3:
        print(f"Título demasiado largo, intentando reducir tamaño: {titulo}")
        titulo = chatGPT(titulo_sistema.format(pregunta=pregunta, keyword=keyword), f"Haz más pequeño el meta título: \"{titulo}\".", titulo_asistente)
        titulo = titulo.replace("\"", "").rstrip(".")
        intentos += 1
    print(f"Título creado: {titulo}")
    return titulo

# Función para crear una investigación
def crear_investigacion(pregunta, competencia):
    print(f"Creando investigación para la pregunta: {pregunta}")
    investigacion = re.sub('\n+', '\n', chatGPT(investigacion_sistema.format(pregunta=pregunta), investigacion_usuario.format(competencia=competencia), investigacion_asistente.format(pregunta=pregunta)))
    return investigacion

# Función para crear la estructura del artículo
def crear_estructura(pregunta, titulo, investigacion):
    print(f"Creando estructura del artículo para el título: {titulo}")
    estructura = f"#{titulo}\n\n{chatGPT(estructura_sistema.format(titulo=titulo), estructura_usuario.format(pregunta=pregunta, investigacion=investigacion), estructura_asistente.format(titulo=titulo))}"
    return estructura

# Función para crear el artículo
def crear_articulo(titulo, keyword, estructura, investigacion):
    print(f"Creando artículo para el título: {titulo}")
    articulo = chatGPT(articulo_sistema.format(titulo=titulo, keyword=keyword, estructura=estructura), articulo_usuario.format(investigacion=investigacion), articulo_asistente.format(titulo=titulo))
    articulo = articulo.replace(".</h", "</h")
    articulo = articulo.replace(":</h", "</h")
    articulo = articulo.replace("# Introducción", "")
    articulo = articulo.replace("## Introducción", "")
    articulo = articulo.replace("### Conclusiones", "")
    articulo = articulo.replace("### Conclusión", "")
    articulo = re.sub(r'En (conclusión|resumen), (\w)', lambda match: match.group(2).upper(), articulo)
    articulo = articulo.replace("En conclusión, ", "").replace("En resumen, ", "")
    articulo = re.sub(r'<strong>En (conclusión|resumen),</strong> (\w)', lambda match: match.group(2).upper(), articulo)
    articulo = articulo.replace("<strong>En conclusión,</strong> ", "").replace("<strong>En resumen,</strong> ", "")
    print(f"Artículo creado para el título: {titulo}")
    return articulo

# Función para crear la descripción del artículo
def crear_descripcion(keyword, estructura):
    print(f"Creando descripción para la keyword: {keyword}")
    descripcion = chatGPT(descripcion_sistema.format(keyword=keyword), descripcion_usuario.format(estructura=estructura), descripcion_asistente)
    descripcion = descripcion.replace("\"", "")
    intentos = 0
    while len(descripcion) > 150 and intentos < 3:
        print(f"Descripción demasiado larga, intentando reducir tamaño: {descripcion}")
        descripcion = chatGPT(descripcion_sistema.format(keyword=keyword), f"Haz más pequeña la meta descripción: \"{descripcion}\".", descripcion_asistente)
        descripcion = descripcion.replace("\"", "")
        intentos += 1
    print(f"Descripción creada: {descripcion}")
    return descripcion

# Función para crear la imagen
def crear_imagen(estructura):
    print("Creando imagen")
    imagen = chatGPT(imagen_sistema, imagen_usuario.format(estructura=estructura), imagen_asistente)
    imagen = imagen.replace("\"", "").rstrip(".")
    print("Imagen creada")
    return imagen

# Función para crear la categoría
def crear_categoria(estructura):
    print("Creando categoría")
    categoria = chatGPT(categoria_sistema, categoria_usuario.format(estructura=estructura), categoria_asistente)
    categoria = unidecode(categoria)
    categoria = categoria.replace("\"", "").rstrip(".")
    print("Categoría creada")
    return categoria

# Función para leer las keywords existentes de un archivo CSV
def leer_keywords_existentes(nombre_archivo):
    print(f"Leyendo keywords existentes del archivo: {nombre_archivo}")
    if not os.path.isfile(nombre_archivo):
        return set()
    with open(nombre_archivo, "r", newline="", encoding="utf-8") as archivo_csv:
        lector = csv.reader(archivo_csv)
        next(lector, None)
        keywords_set = {fila[0] for fila in lector}
        print(f"Keywords existentes leídas: {keywords_set}")
        return keywords_set

# Función para guardar el resultado en un archivo MDX
def guardar_resultado_en_markdown(titulo, resultado):
    print(f"Guardando resultado en archivo markdown para el título: {titulo}")
    slug = slugify.slugify(titulo)
    directorio = "resultados_markdown"
    if not os.path.exists(directorio):
        os.makedirs(directorio)
    archivo_md = f"{directorio}/{slug}.mdx"
    try:
        with open(archivo_md, "w", encoding="utf-8") as md_file:
            md_file.write(resultado)
        print(f"Resultado guardado en: {archivo_md}")
    except IOError as e:
        print(f"Error al guardar el archivo {archivo_md}: {e}")

# Función principal para procesar una keyword
def procesar_keyword(keyword):
    global contador_keywords
    print(f"Procesando keyword: {keyword}")
    resultados_organicos = obtenerValueSERP(keyword)
    titulos = "\n".join([res.get('title', '') for res in resultados_organicos])
    pregunta = crear_pregunta(keyword, titulos)
    titulo = crear_titulo(pregunta, keyword, titulos)
    investigacion = ""
    for resultado_organico in resultados_organicos:
        competencia = Article(resultado_organico.get('link', ''))
        hilo_descarga = threading.Thread(target=descargar_articulo, args=(competencia,))
        hilo_descarga.start()
        hilo_descarga.join(timeout=60)
        if not hilo_descarga.is_alive():
            competencia = competencia.text
            competencia = ' '.join(competencia.split()[:3000])
            if competencia:
                investigacion = crear_investigacion(pregunta, competencia)
                break
    if not investigacion:
        investigacion = pregunta
    estructura = crear_estructura(pregunta, titulo, investigacion)
    articulo = crear_articulo(titulo, keyword, estructura, investigacion)
    descripcion = crear_descripcion(keyword, estructura)
    categoria = crear_categoria(estructura)
    
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Crear el contenido MDX
    resultado_mdx = f"""
---
title: '{titulo}'
date: {fecha_actual}
tags: {categoria}
draft: false
summary: '{descripcion}'
---
{articulo}
"""
    guardar_resultado_en_markdown(titulo, resultado_mdx)
    
    contador_keywords += 1
    print(f"Progreso: {contador_keywords}/{total_keywords} | Keyword: {keyword} | Título: {titulo}")

# Leer las keywords existentes y obtener las faltantes
keywords_existentes = leer_keywords_existentes("3._Articulos.csv")
keywords_faltantes = [kw for kw in keywords if kw not in keywords_existentes]
total_keywords = len(keywords_faltantes)
print(f"Total de keywords a procesar: {total_keywords}")

# Utilizar ThreadPoolExecutor para procesar las keywords en paralelo
with concurrent.futures.ThreadPoolExecutor(max_workers=64) as ejecutor:
    futures = [ejecutor.submit(procesar_keyword, kw) for kw in keywords_faltantes]
    concurrent.futures.wait(futures)
print("Script finalizado")
