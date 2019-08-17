from flask import Flask, render_template, request, json, jsonify
import os
import json
import numpy as np
import io
from PIL import Image

import math
import base64

from watson_machine_learning_client import WatsonMachineLearningAPIClient
from wiotp.sdk.application import ApplicationClient

app = Flask(__name__)
app.config.from_object(__name__)
port = int(os.getenv('PORT', 8080))

volumeSemiesfera = 2 * math.pi / 3
myConfig = {
    "auth": {
        "key": "a-y76ylb-ckj29x2v6b",
        "token": "IoZc5eC_lxrtJdmi4O"
    }
}
client = ApplicationClient(config=myConfig)
# eventData = None


# def sensorCallback(event):
#     print("Vamos")
#     print(event)
#     eventData = json.dump(event.data)


client.connect()
# client.deviceEventCallback = sensorCallback
# client.subscribeToDeviceEvents(
#     typeId="maratona", deviceId="d9", eventId="sensor")


@app.route("/", methods=['GET'])
def hello():
    error = None
    return render_template('index.html', error=error)


def fahrenheitFromCelsius(celsius):
    return (celsius * 9 / 5) + 32


def itu(temp, ur):
    return temp - 0.55 * (1 - ur) * (temp - 14)


@app.route("/iot", methods=['GET'])
def result():
    print(request)

    # Implemente sua lógica aqui e insira as respostas na variável 'resposta'

    device = {"typeId": "maratona", "deviceId": "d9"}
    event = "sensor"
    event = client.lec.get(device, event)
    eventData = json.loads(base64.b64decode(event.payload).decode("utf-8"))

    resposta = {
        "iotData": eventData["data"],
        "itu": itu(eventData["data"]["temperatura"], eventData["data"]["umidade_ar"]),
        "volumeAgua": eventData["data"]["umidade_solo"] * volumeSemiesfera,
        "fahrenheit": fahrenheitFromCelsius(eventData["data"]["temperatura"])
    }
    response = app.response_class(
        response=json.dumps(resposta),
        status=200,
        mimetype='application/json'
    )
    return response


def prepare_image(image):
    image = image.resize(size=(96, 96))
    image = np.array(image, dtype="float") / 255.0
    image = np.expand_dims(image, axis=0)
    image = image.tolist()
    return image


@app.route('/predict', methods=['POST'])
def predict():
    print(request)
    image = request.files["image"].read()
    image = Image.open(io.BytesIO(image))
    image = prepare_image(image)

    # Faça uma requisição para o serviço Watson Machine Learning aqui e retorne a classe detectada na variável 'resposta'
    # Credenciais do Watson Machine Learning
    wml_credentials = {
        "apikey": "K9SRZk1WdW9oA_uEbSUV6IBDnYOz5RC8FTSnqB0pWiPT",
        "iam_apikey_description": "Auto-generated for key 8d98bf3c-518d-492f-a271-d0b6b7ebd362",
        "iam_apikey_name": "wdp-writer",
        "iam_role_crn": "crn:v1:bluemix:public:iam::::serviceRole:Writer",
        "iam_serviceid_crn": "crn:v1:bluemix:public:iam-identity::a/1de11f71360f42fd9ba01f2b76bced35::serviceid:ServiceId-e809b862-d7cc-4230-8f62-7c56d45935f2",
        "instance_id": "f872faaa-1d3b-4d8a-9cf7-1eef9672debb",
        "url": "https://us-south.ml.cloud.ibm.com"
    }
    client = WatsonMachineLearningAPIClient(wml_credentials)

    # # Definição de metadados do modelo (versao de python, framework, libs e etc)
    # sample_saved_model_filename = 'model_WSTUDIO.tar.gz'
    # metadata = {
    #     client.repository.ModelMetaNames.NAME: 'MY_FIRST_SUBMIT',
    #     client.repository.ModelMetaNames.FRAMEWORK_NAME: 'tensorflow',
    #     client.repository.ModelMetaNames.FRAMEWORK_VERSION: '1.11',
    #     client.repository.ModelMetaNames.RUNTIME_NAME: 'python',
    #     client.repository.ModelMetaNames.RUNTIME_VERSION: '3.6',
    #     client.repository.ModelMetaNames.FRAMEWORK_LIBRARIES:  [{"name": "keras", "version": "2.2.4"}]
    # }

    # # Conexão com o WML
    # model_details = client.repository.store_model(
    #     sample_saved_model_filename, meta_props=metadata, training_data=None)

    # # Deploy do modelo
    # model_id = model_details["metadata"]["guid"]
    # model_deployment_details = client.deployments.create(
    #     artifact_uid=model_id, name="MY FIRST SUBMIT D9 Behind The Code")

    # # Retrieve da URL da API para consumo da mesma
    # model_endpoint_url = client.deployments.get_scoring_url(
    #     model_deployment_details)
    # client.deployments.get_scoring_url()
    # print("A URL de chamada da sua API é : ", model_endpoint_url)
    # ####
    model_endpoint_url = "https://us-south.ml.cloud.ibm.com/v3/wml_instances/f872faaa-1d3b-4d8a-9cf7-1eef9672debb/deployments/3250b14b-3ec3-4c75-8165-8a0e58bed380/online"

    data = client.deployments.score(model_endpoint_url, image)

    resposta = {
        "class": data
    }
    return resposta


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
