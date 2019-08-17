from flask import Flask, render_template, request, json, jsonify
import os
import json
import numpy as np
import io
from PIL import Image

import math
import base64

from keras.preprocessing import image as Kimage
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
    ai_parms = {"wml_credentials": 'wml_credentials',
                "model_endpoint_url": model_endpoint_url}

    # Load da imagem de teste e pre-processing da mesma - para entrada na rede neural convolucional
    image = Kimage.load_img("teste2.jpg")
    plt.imshow(image)
    image = image.resize(size=(96, 96))
    image = img_to_array(image)
    image = np.array(image, dtype="float") / 255.0
    image = np.expand_dims(image, axis=0)
    image = image.tolist()

    # Chamada da função SCORE no modelo (inference)
    model_payload = {"values": image}
    model_result = client.deployments.score(
        ai_parms["model_endpoint_url"], model_payload)
    print(model_result)

    classes = ['CLEAN', 'DIRTY']
    print("Imagem Classificada como : ",
          classes[model_result['values'][0][1][0]])

    print("Probabilidades : \n\t",
          classes[model_result['values'][0][1][0]], " : %.2f" % (
              model_result['values'][0][0][0]*100), "%\n\t",
          )

    resposta = {
        "class": classes[model_result['values'][0][1][0]]
    }
    return resposta


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
