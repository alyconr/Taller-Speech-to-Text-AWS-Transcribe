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
# # 3. Nombre del JOB

# %%
#Importamos la librería que manipula la fecha y hora
from datetime import datetime

#Obtenemos la fecha y hora actual
fecha = datetime.today()

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

#Colocamos el nombre del JOB de la transcripción
nombreDelJob = f"transcripcion-bda-{fechaStr}"

#Verificamos
print(nombreDelJob)

# %% [markdown]
# # 4. Corte del audio

# %%
#Descargamos el audio desde AWS
s3.download_file(
  bucket,
  "content/AUDIO_CALL_CENTER.wav",
  "./content/AUDIO_CALL_CENTER.wav"
)

# %%
#Definimos el tiempo de corte de los "chunks" (partes del audio)
tiempoDeChunkMilisegundos = 5000

# %%
#Utilitario para cortar el audio en partes
from pydub import AudioSegment

# %%
#Definimos el tiempo de corte de los "chunks" (partes del audio)
tiempoDeChunkMilisegundos = 5000

# %%
#Leemos el archivo de audio
audio = AudioSegment.from_file("./content/AUDIO_CALL_CENTER.wav")

# %%
#Variable que acumula cada corte del archivo
audioChunks = []

# %%
#Cortamos el archivo, desde el bit "0", hasta el tamaño del audio [len(audio)], con un tamaño de corte "tiempoDeChunkMilisegundos"
for i in range(0, len(audio), tiempoDeChunkMilisegundos):
    #Obtenemos el corte desde el bit "i" hasta el bit "i + tiempoDeChunkMilisegundos"
    chunk = audio[i : i + tiempoDeChunkMilisegundos]

    #Definimos el nombre del archivo de esa parte del audio
    archivoChunk = "./content/chunk_"+str(i)+".wav"

    #Guardamos el archivo en formato "wav"
    chunk.export(archivoChunk, format = "wav")

    #Guardamos la ruta del archivo en
    audioChunks.append(archivoChunk)

# %%
#Verificamos
audioChunks

# %%
#Definimos un indice
i = 0

# %%
#Subimos cada archivo a AWS
for audioChunk in audioChunks:

  #Subimos el archivo a AWS
  s3.upload_file(
    audioChunk,
    bucket,
    f"audios/chunk_{i}.wav"
  )

  #Aumentamos el indice en 1
  i = i + 1

# %% [markdown]
# # 5. Envío de consulta

# %%
#Indice para enumerar cada job de cada chunk
i = 0

# %%
#Array que almacena todos los nombres de jobs que están procesando todos los chunks
nombresJobs = []

# %%
#Iteramos cada chunk
for chunk in audioChunks:
  #Definimos el nombre del job
  nombreDeJobParaElChunk = nombreDelJob + "-" + str(i)

  #Imprimos el nombre del JOB
  print(nombreDeJobParaElChunk)

  #Lo almacenamos en el array
  nombresJobs.append(nombreDeJobParaElChunk)

  #Enviamos la consulta
  #Es una consulta asíncrona
  respuesta = transcribe.start_transcription_job(
      TranscriptionJobName = nombreDeJobParaElChunk, #Nombre del JOB
      LanguageCode = "es-ES", #Idioma del audio
      MediaFormat = "wav", #Formato del audio
      Media = {
          "MediaFileUri": f"s3://{bucket}/audios/chunk_{i}.wav", #Ruta del chunk
      }
  )

  #Aumentamos el índice
  i = i + 1

# %%
#Verificamos los nombres de JOBS
nombresJobs

# %% [markdown]
# # 6. Bucle de espera hasta la finalización del proceso

# %%
#Array que almacena los estados de los jobs
estados = []

# %%
#Obtenemos el estado de todos los jobs
for nombreDelJob in nombresJobs:
  #Obtenemos el job según su nombre
  proceso = transcribe.get_transcription_job(TranscriptionJobName = nombreDelJob)

  #Obtenemos el estado
  estado = proceso["TranscriptionJob"]["TranscriptionJobStatus"]

  #Verificamos el estado
  print(estado)

  #Lo agregamos al array
  estados.append(estado)

# %%
#Verificamos
estados

# %%
#Verificamos que los tres estados estén en "COMPLETED" o en "FAILED"
#Cantidad de jobs
cantidadDeJobs = len(nombresJobs)

#Verificamos
cantidadDeJobs

# %%
#Cuenta cuántos procesos han finalizado
cantidadDeJobsFinalizados = 0

# %%
#Verificamos
for estado in estados:

  #Verificamos el estado
  if estado in ["COMPLETED", "FAILED"]:
    #Aumentamos la cantidad de procesos finalizados en 1
    cantidadDeJobsFinalizados = cantidadDeJobsFinalizados + 1

# %%
#Verificamos
if cantidadDeJobs == cantidadDeJobsFinalizados:
  print("Proceso finalizado!")
else:
  print(f"Procesando {cantidadDeJobsFinalizados} de {cantidadDeJobs}")

# %%
#Librería para pausar el código
import time

# %% [markdown]
# # 7. Envío de consulta con chunks y bucle de espera

# %%
#OBTENEMOS EL NOMBRE DEL JOB
#Importamos la librería que manipula la fecha y hora
from datetime import datetime

#Obtenemos la fecha y hora actual
fecha = datetime.today()

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

#Colocamos el nombre del JOB de la transcripción
nombreDelJob = f"transcripcion-bda-{fechaStr}"

#Verificamos
print(nombreDelJob)

# %%
#ENVIAMOS LA CONSULTA
#Indice para enumerar cada job de cada chunk
i = 0

#Array que almacena todos los nombres de jobs que están procesando todos los chunks
nombresJobs = []

#Iteramos cada chunk
for chunk in audioChunks:
  #Definimos el nombre del job
  nombreDeJobParaElChunk = nombreDelJob + "-" + str(i)

  #Imprimos el nombre del JOB
  print(nombreDeJobParaElChunk)

  #Lo almacenamos en el array
  nombresJobs.append(nombreDeJobParaElChunk)

  #Enviamos la consulta
  #Es una consulta asíncrona
  respuesta = transcribe.start_transcription_job(
      TranscriptionJobName = nombreDeJobParaElChunk, #Nombre del JOB
      LanguageCode = "es-ES", #Idioma del audio
      MediaFormat = "wav", #Formato del audio
      Media = {
          "MediaFileUri": f"s3://{bucket}/audios/chunk_{i}.wav", #Ruta del chunk
      }
  )

  #Aumentamos el índice
  i = i + 1

# %%
#Librería para pausar el código
import time

#Entramos en bucle infinito
#TIEMPO: 1 MINUTO
while True:

  #Array que almacena los estados de los jobs
  estados = []

  #Obtenemos el estado de todos los jobs
  for nombreDelJob in nombresJobs:
    #Obtenemos el job según su nombre
    proceso = transcribe.get_transcription_job(TranscriptionJobName = nombreDelJob)

    #Obtenemos el estado
    estado = proceso["TranscriptionJob"]["TranscriptionJobStatus"]

    #Lo agregamos al array
    estados.append(estado)

  #Verificamos que los tres estados estén en "COMPLETED" o en "FAILED"
  #Cantidad de jobs
  cantidadDeJobs = len(nombresJobs)

  #Cuenta cuántos procesos han finalizado
  cantidadDeJobsFinalizados = 0

  #Verificamos
  for estado in estados:

    #Verificamos el estado
    if estado in ["COMPLETED", "FAILED"]:
      #Aumentamos la cantidad de procesos finalizados en 1
      cantidadDeJobsFinalizados = cantidadDeJobsFinalizados + 1

  #Verificamos
  if cantidadDeJobs == cantidadDeJobsFinalizados:
    #Indicamos la finalización del proceso
    print("Proceso finalizado!")

    #Si finalizó, salimos del bucle infinito
    break
  else:
    #Mostramos el estado del proceso
    print(f"Procesando {cantidadDeJobsFinalizados} de {cantidadDeJobs}")

  #Detenemos el código por 5 segundos antes de repetir el bucle
  time.sleep(5)

# %% [markdown]
# # 8. Extracción de la respuesta

# %%
#Variable que acumula los textos de los chunks de audio
transcripcionCompleta = ""

# %%
#Librería para descargar desde enlaces
import requests

#Librería para manipular JSONs
import json

#Obtenemos los textos de cada job
for nombreDelJob in nombresJobs:
  print(f"Extrayendo texto del job {nombreDelJob}")

  #Obtenemos el job según su nombre
  proceso = transcribe.get_transcription_job(TranscriptionJobName = nombreDelJob)

  #Definimos la URL en donde se encuentra la transcripción
  urlDeTranscripcion = proceso["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]

  #Descargamos el archivo
  archivo = requests.get(urlDeTranscripcion)

  #Convertimos el contenido del archivo en un JSON
  archivoJson = archivo.json()

  #Extraemos la transcripción
  transcripcion = archivoJson["results"]["transcripts"][0]["transcript"]

  #Mostramos la transcripcion
  print(transcripcion)

  #Acumulamos la transcripcion
  transcripcionCompleta = transcripcionCompleta + " " + transcripcion

# %%
#Verificamos
transcripcionCompleta

# %% [markdown]
# # 9. Almacenamiento

# %%
#Abrimos un archivo en modo escritura
with open("./content/transcripcion.txt", "w") as archivo:
    #Escribimos el contenido en el archivo
    archivo.write(transcripcionCompleta)

#Obtenemos el cliente de servicio
s3 = boto3.client(
  "s3", #Servicio al que nos conectamos
  aws_access_key_id = access_key_id, #Identificador de la clave
  aws_secret_access_key = secret_access_key, #Contraseña de la clave
  region_name = region #Región de la clave
)

#Subimos el archivo a AWS
s3.upload_file(
  "./content/transcripcion.txt",
  bucket,
  "output/transcripcion.txt"
)

#Verificamos desde el portal de AWS


