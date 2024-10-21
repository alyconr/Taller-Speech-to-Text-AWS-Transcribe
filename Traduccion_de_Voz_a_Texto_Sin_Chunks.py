# %% [markdown]
# # 1. Preparación de Entorno

# %%
from dotenv import load_dotenv

import os

# Carga las variables de entorno desde el archivo .env
load_dotenv()

bucket = "datasetsaudio"

#Utilitario para manifrompular los servicios de AWS
import boto3

# %%
access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region = os.getenv('AWS_DEFAULT_REGION')

# %% [markdown]
# # 2. Conexión al servicio

# %%
#Obtenemos el cliente de servicio
transcribe = boto3.client(
  "transcribe", #Servicio al que nos conectamos
  aws_access_key_id = access_key_id, #Identificador de la clave
  aws_secret_access_key = secret_access_key, #Contraseña de la clave
  region_name = region #Región de la clave
)

# %%
#También necesitaremos el cliente del S3
s3 = boto3.client(
  "s3", #Servicio al que nos conectamos
  aws_access_key_id = access_key_id, #Identificador de la clave
  aws_secret_access_key = secret_access_key, #Contraseña de la clave
  region_name = region #Región de la clave
)

# %% [markdown]
# # 3. Envío de consulta

# %%
#Importamos la librería que manipula la fecha y hora
from datetime import datetime

# %%
#Obtenemos la fecha y hora actual
fecha = datetime.today()

# %%
# Formateamos la fecha y hora
# Extraemos:
#
# - El año: %Y
# - El mes: %m
# - El día: %d
# - La hora: %H
# - El minuto: %M
# - El segundo: %S
# - El microsegundo: %f
fechaStr = fecha.strftime("%Y%m%d%H%M%S%f")

#Verificamos
fechaStr

# %%
#Colocamos el nombre del JOB de la transcripción
nombreDelJob = f"transcripcion-bda-{fechaStr}"

#Verificamos
print(nombreDelJob)

# %%
#Enviamos la consulta
#Es una consulta asíncrona
respuesta = transcribe.start_transcription_job(
    TranscriptionJobName = nombreDelJob, #Nombre del JOB
    LanguageCode = "es-ES", #Idioma del audio
    MediaFormat = "wav", #Formato del audio
    Media = {
        "MediaFileUri": f"s3://{bucket}/content/AUDIO_CALL_CENTER.wav", #Ruta del audio
    }
)

# %% [markdown]
# # 4. Bucle de espera hasta la finalización del proceso

# %%
#Obtenemos el job según su nombre
proceso = transcribe.get_transcription_job(TranscriptionJobName = nombreDelJob)

# %%
#Verificamos el estado
proceso["TranscriptionJob"]["TranscriptionJobStatus"]

# %%
#Librería para pausar el código
import time 

# %%
#Entramos en bucle infinito
#TIEMPO: 1 MINUTO
while True:

  #Obtenemos el job según su nombre
  proceso = transcribe.get_transcription_job(TranscriptionJobName = nombreDelJob)

  #Verificamos el estado
  if proceso["TranscriptionJob"]["TranscriptionJobStatus"] in ["COMPLETED", "FAILED"]:
    #Indicamos la finalización del proceso
    print("Proceso finalizado!")

    #Si finalizó, salimos del bucle infinito
    break
  else:
    #Mostramos el estado del proceso
    print(proceso["TranscriptionJob"]["TranscriptionJobStatus"])

  #Detenemos el código por 5 segundos antes de repetir el bucle
  time.sleep(5)

# %% [markdown]
# # 5. Análisis de la respuesta

# %%
#Obtenemos el job según su nombre
proceso = transcribe.get_transcription_job(TranscriptionJobName = nombreDelJob)

#Mostramos el estado del proceso
print(proceso["TranscriptionJob"]["TranscriptionJobStatus"])

# %%
#Vemos el contenido
proceso

# %%
#Definimos la URL en donde se encuentra la transcripción
urlDeTranscripcion = proceso["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]

#Verificamos y entramos a la URL para ver el contenido
print(urlDeTranscripcion)

# %%
#Librería para descargar desde enlaces
import requests

# %%
    #Librería para manipular JSONs
import json

# %%
#Descargamos el archivo
archivo = requests.get(urlDeTranscripcion)

# %%
#Convertimos el contenido del archivo en un JSON
archivoJson = archivo.json()

#Verificamos
print(archivoJson)

# %%
#Extraemos la transcripción
archivoJson["results"]["transcripts"][0]["transcript"]


