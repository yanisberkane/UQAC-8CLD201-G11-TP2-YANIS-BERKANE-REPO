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

@app.blob_trigger(arg_name="myblob", path=IMG_PATH,
                               connection="AzureWebJobsStorage")
def blob_trigger(myblob: func.InputStream):
    try:
        # Extract filename
        filename = myblob.name.split("/")[-1]
        logging.info(f"Python blob trigger function processed blob"
                     f"\nName: {filename}")

        # Send filename to Service Bus queue
        with ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STR) as client:
            sender = client.get_queue_sender(queue_name=QUEUE_NAME)
            with sender:
                message = ServiceBusMessage(filename)
                sender.send_messages(message)
                logging.info(f"Filename '{filename}' sent to queue '{QUEUE_NAME}'")

    except Exception as e:
        logging.error(f"Error: {e}")
