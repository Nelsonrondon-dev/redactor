import concurrent.futures
import threading
import openai
import requests
from typing import Callable

# Definición de nombres de archivos
ARCHIVO_VALUESERP = "0._ValueSERP.txt"
ARCHIVO_OPENAI = "1._OpenAI.txt"
bloqueo = threading.Lock()

# Clase para manejar archivos de claves
class ManejadorArchivoClaves:
    @staticmethod
    def leer_claves(nombre_archivo: str) -> set:
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            return {linea.strip() for linea in archivo}
    
    @staticmethod
    def escribir_claves(nombre_archivo: str, claves: set):
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            for clave in claves:
                archivo.write(clave + "\n")

# Clase para validar claves
class ValidadorClaves:
    def __init__(self, nombre_archivo: str, validador: Callable, consulta_prueba: str):
        self.nombre_archivo = nombre_archivo
        self.validador = validador
        self.consulta_prueba = consulta_prueba
        self.claves = ManejadorArchivoClaves.leer_claves(nombre_archivo)
    
    def ejecutar(self):
        self._procesar_claves()
        ManejadorArchivoClaves.escribir_claves(self.nombre_archivo, self.claves)
    
    def _procesar_claves(self):
        def validar_clave(clave):
            if not self.validador(self.consulta_prueba, clave):
                with bloqueo:
                    self.claves.discard(clave)
        
        # Validación de claves en paralelo utilizando ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
            executor.map(validar_clave, self.claves)

# Función para validar claves de ValueSERP
def validarValueSERP(consulta: str, clave: str) -> bool:
    for intento in range(3):
        try:
            respuesta = requests.get('https://api.valueserp.com/search', params={'api_key': clave, 'q': consulta}, timeout=60)
            if respuesta.status_code == 200:
                resultados = respuesta.json().get('organic_results', [])
                if resultados:
                    print(f"ValueSerp {clave[:3]}: Correcta")
                    return True
        except Exception as e:
            print(f"ValueSerp {clave[:3]}: Error {intento + 1}/{3}.")
    return False

# Función para validar claves de OpenAI
def validarOpenAI(usuario: str, clave: str) -> bool:
    for intento in range(3):
        try:
            openai.api_key = clave
            openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": usuario}]
            )
            print(f"OpenAI {clave[:6]}: Correcta")
            return True
        except Exception as e:
            print(f"OpenAI {clave[:6]}: Error {intento + 1}/{3}.")
    return False

# Instancias de validadores y ejecución
validador_openai = ValidadorClaves(ARCHIVO_OPENAI, validarOpenAI, "hola")
validador_openai.ejecutar()
validador_valueserp = ValidadorClaves(ARCHIVO_VALUESERP, validarValueSERP, "hola")
validador_valueserp.ejecutar()
