from flask import Flask, request, jsonify
import requests
from io import BytesIO

app = Flask(__name__)

TOKEN_URL = 'https://www.nyckel.com/connect/token'
NYCKEL_CLIENT_ID = 't5b9np1au0xo5bgu534hd8bt9z3uo0xt'
NYCKEL_CLIENT_SECRET = 'p23uy4bkuinga2fn83wvy40ltizol6mu24y27lv1skmvkui7jgmk31ul1h1f4mzo'
PREDICTION_URL = 'https://www.nyckel.com/v1/functions/dog-breed-identifier/invoke'

def get_access_token():
    data = {
        'grant_type': 'client_credentials',
        'client_id': NYCKEL_CLIENT_ID,
        'client_secret': NYCKEL_CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"Erro ao obter o token: {response.status_code} {response.text}")

@app.route('/')
def hello_world():
    return "Hello World testing"

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "Nenhuma imagem enviada"}), 400

    image = request.files['image']
    image_bytes = image.read()

    try:
        token = get_access_token()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    headers = {'Authorization': f'Bearer {token}'}
    files = {'data': ('image.jpg', image_bytes, 'image/jpeg')}
    response = requests.post(PREDICTION_URL, headers=headers, files=files)

    if response.status_code == 200:
        result = response.json()
        return jsonify({
            "message": "Raça identificada com sucesso!",
            "prediction": result
        }), 200
    else:
        return jsonify({
            "error": f"Erro ao usar o Nyckel: {response.status_code} {response.text}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True)