import azure.functions as func
import logging
import os, io
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.storage.blob import BlobServiceClient
from PIL import Image, ImageDraw, ImageFont

app = func.FunctionApp()

# Read environment variables
SERVICE_BUS_CONNECTION_STR = os.getenv("SERVICE_BUS_CONN_STR")
QUEUE_NAME = os.getenv("QUEUE_NAME")
BLOB_CONTAINER = os.getenv("BLOB_CONTAINER_NAME")
PROCESSED_BLOB_CONTAINER = os.getenv("PROCESSED_BLOB_CONTAINER_NAME")
IMG_PATH = BLOB_CONTAINER + "/{name}.png"

@app.service_bus_queue_trigger(arg_name="azservicebus", queue_name=QUEUE_NAME,
                               connection="SERVICE_BUS_CONN_STR") 
def servicebus_trigger(azservicebus: func.ServiceBusMessage):
    try:
        # Lire le message de la queue
        filename = azservicebus.get_body().decode('utf-8')
        logging.info(f"Processing file: {filename}")

        # Connexion au stockage Blob
        blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AzureWebJobsStorage"))
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER)

        # Récupérer le blob original
        blob_client = container_client.get_blob_client(f"{filename}")
        blob_data = blob_client.download_blob().readall()

        # Charger l'image
        image = Image.open(io.BytesIO(blob_data))

        # Ajouter un watermark ou redimensionner l'image
        watermark_text = "TP2 - Azure Functions - UQAC"
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()

        # Obtenir la taille du texte avec textbbox (disponible dans les versions récentes de Pillow)
        text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Position du texte (en bas à droite de l'image)
        text_position = (image.size[0] - text_width - 10, image.size[1] - text_height - 10)

        # Dessiner le texte (watermark) sur l'image
        draw.text(text_position, watermark_text, fill=(255, 255, 255), font=font)


        # Sauvegarder l'image traitée
        output = io.BytesIO()
        new_filename = f"processed_{filename}"
        image.save(output, format="PNG")
        output.seek(0)

        # Télécharger l'image dans un nouveau conteneur
        processed_blob_client = blob_service_client.get_blob_client(container=PROCESSED_BLOB_CONTAINER, blob=new_filename)
        processed_blob_client.upload_blob(output)
        logging.info(f"Processed file '{new_filename}' uploaded to '{PROCESSED_BLOB_CONTAINER}' container.")

        # Supprimer l'image originale
        blob_client.delete_blob()
        logging.info(f"Original file '{filename}' deleted.")

    except Exception as e:
        logging.error(f"Error processing message: {e}")
