## Tabla de Contenidos

1.  [Introducción](#introducci%C3%B3n)
2.  [¿Qué es Amazon Transcribe?](#qu%C3%A9-es-amazon-transcribe)
3.  [Preparación del Entorno](#preparaci%C3%B3n-del-entorno)
4.  [Speech to Text con Chunks](#speech-to-text-con-chunks)
5.  [Speech to Text sin Chunks](#speech-to-text-sin-chunks)
6.  [Comparación de Métodos](#comparaci%C3%B3n-de-m%C3%A9todos)
7.  [Conclusión](#conclusi%C3%B3n)

## Introducción

Este taller explora cómo utilizar Amazon Transcribe para crear un modelo de Speech to Text (STT) enfocado en transcribir conversaciones de call center. Presentaremos dos métodos: uno que procesa el audio en chunks (segmentos) y otro que procesa el archivo de audio completo.

## ¿Qué es Amazon Transcribe?

Amazon Transcribe es un servicio de reconocimiento automático de voz (ASR) que utiliza modelos de aprendizaje profundo para convertir audio en texto. Ofrece características como reconocimiento de múltiples hablantes, puntuación automática, y filtrado de vocabulario personalizado.

## Preparación del Entorno

Antes de comenzar, necesitamos configurar nuestro entorno:

```python
    from dotenv import load_dotenv
import os
import boto3

# Carga las variables de entorno desde el archivo .env
load_dotenv()

bucket = "datasetsaudio"

access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region = os.getenv('AWS_DEFAULT_REGION')

# Configuración de los clientes de AWS
transcribe = boto3.client(
    "transcribe",
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name=region
)

s3 = boto3.client(
    "s3",
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name=region
)
```

## Speech to Text con Chunks

Este método divide el audio en segmentos más pequeños antes de procesarlo.

### Pasos principales:

1.  Preparación del audio
2.  Corte del audio en chunks
3.  Envío de consultas para cada chunk
4.  Espera y monitoreo de los procesos
5.  Extracción y combinación de resultados

```python

import time
from datetime import datetime
from pydub import AudioSegment
import requests
import json

# Generar nombre único para el job
fecha = datetime.today()
fechaStr = fecha.strftime("%Y%m%d%H%M%S%f")
nombreDelJob = f"transcripcion-bda-{fechaStr}"

# Descargar y cortar el audio
s3.download_file(bucket, "content/AUDIO_CALL_CENTER.wav", "./content/AUDIO_CALL_CENTER.wav")
tiempoDeChunkMilisegundos = 5000
audio = AudioSegment.from_file("./content/AUDIO_CALL_CENTER.wav")
audioChunks = []

for i in range(0, len(audio), tiempoDeChunkMilisegundos):
    chunk = audio[i : i + tiempoDeChunkMilisegundos]
    archivoChunk = f"./content/chunk_{i}.wav"
    chunk.export(archivoChunk, format="wav")
    audioChunks.append(archivoChunk)

# Subir chunks a S3 y iniciar trabajos de transcripción
nombresJobs = []
for i, audioChunk in enumerate(audioChunks):
    s3.upload_file(audioChunk, bucket, f"audios/chunk_{i}.wav")
    nombreDeJobParaElChunk = f"{nombreDelJob}-{i}"
    nombresJobs.append(nombreDeJobParaElChunk)
    transcribe.start_transcription_job(
        TranscriptionJobName=nombreDeJobParaElChunk,
        LanguageCode="es-ES",
        MediaFormat="wav",
        Media={"MediaFileUri": f"s3://{bucket}/audios/chunk_{i}.wav"}
    )

# Esperar a que todos los jobs finalicen
while True:
    estados = [transcribe.get_transcription_job(TranscriptionJobName=job)["TranscriptionJob"]["TranscriptionJobStatus"] for job in nombresJobs]
    if all(estado in ["COMPLETED", "FAILED"] for estado in estados):
        print("Todos los procesos han finalizado")
        break
    time.sleep(5)

# Extraer y combinar resultados
transcripcionCompleta = ""
for nombreDelJob in nombresJobs:
    proceso = transcribe.get_transcription_job(TranscriptionJobName=nombreDelJob)
    urlDeTranscripcion = proceso["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
    archivo = requests.get(urlDeTranscripcion)
    archivoJson = archivo.json()
    transcripcion = archivoJson["results"]["transcripts"][0]["transcript"]
    transcripcionCompleta += " " + transcripcion

# Guardar resultado
with open("./content/transcripcion.txt", "w") as archivo:
    archivo.write(transcripcionCompleta)

s3.upload_file("./content/transcripcion.txt", bucket, "output/transcripcion.txt")
```

## Speech to Text sin Chunks

Este método procesa el archivo de audio completo de una vez.

### Pasos principales:

1.  Envío de la consulta para el archivo completo
2.  Espera y monitoreo del proceso
3.  Extracción del resultado

```python
`
from datetime import datetime
import time
import requests
import json

# Generar nombre único para el job
fecha = datetime.today()
fechaStr = fecha.strftime("%Y%m%d%H%M%S%f")
nombreDelJob = f"transcripcion-bda-{fechaStr}"

# Iniciar trabajo de transcripción
transcribe.start_transcription_job(
    TranscriptionJobName=nombreDelJob,
    LanguageCode="es-ES",
    MediaFormat="wav",
    Media={"MediaFileUri": f"s3://{bucket}/content/AUDIO_CALL_CENTER.wav"}
)

# Esperar a que el job finalice
while True:
    proceso = transcribe.get_transcription_job(TranscriptionJobName=nombreDelJob)
    if proceso["TranscriptionJob"]["TranscriptionJobStatus"] in ["COMPLETED", "FAILED"]:
        print("Proceso finalizado!")
        break
    time.sleep(5)

# Extraer resultado
urlDeTranscripcion = proceso["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
archivo = requests.get(urlDeTranscripcion)
archivoJson = archivo.json()
transcripcion = archivoJson["results"]["transcripts"][0]["transcript"]

# Guardar resultado
with open("./content/transcripcion.txt", "w") as archivo:
    archivo.write(transcripcion)

s3.upload_file("./content/transcripcion.txt", bucket, "output/transcripcion.txt")
```

## Comparación de Métodos

1.  **Speech to Text con Chunks**:
    - Ventajas: Mejor para archivos grandes, posibilidad de procesamiento en paralelo.
    - Desventajas: Puede perder contexto entre chunks, requiere más código y manejo.
2.  **Speech to Text sin Chunks**:
    - Ventajas: Más simple de implementar, mantiene mejor el contexto general.
    - Desventajas: Puede ser más lento para archivos muy grandes.

## Conclusión

Ambos métodos tienen sus ventajas y aplicaciones específicas. El método con chunks es ideal para archivos de audio muy largos o cuando se necesita procesamiento en tiempo real. El método sin chunks es más simple y adecuado para archivos de tamaño moderado donde la precisión del contexto es crucial. La elección entre uno u otro dependerá de las necesidades específicas de tu proyecto y las características de tus archivos de audio.

## Autores

Este taller fue desarrollado por:

- Jeysson Aly Contreras
  - LinkedIn: [https://www.linkedin.com/in/jeysson-aly-contreras/](https://www.linkedin.com/in/jeysson-aly-contreras/)
  - GitHub: [https://github.com/alyconr](https://github.com/alyconr)

Si tienes preguntas sobre este taller o estás interesado en colaborar en proyectos similares, no dudes en conectarte a través de LinkedIn o revisar mis proyectos en GitHub.
