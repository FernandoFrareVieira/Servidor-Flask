from flask import Flask, request, jsonify
import requests
import mysql.connector
from mysql.connector import pooling

app = Flask(__name__)

# Configurações do banco de dados
DB_HOST = '35.247.232.121'
DB_USER = 'alano'
DB_PASSWORD = '1234'
DB_NAME = 'db_cachorros'

# Configurações da API Nyckel
TOKEN_URL = 'https://www.nyckel.com/connect/token'
NYCKEL_CLIENT_ID = 't5b9np1au0xo5bgu534hd8bt9z3uo0xt'
NYCKEL_CLIENT_SECRET = 'p23uy4bkuinga2fn83wvy40ltizol6mu24y27lv1skmvkui7jgmk31ul1h1f4mzo'
BREED_PREDICTION_URL = 'https://www.nyckel.com/v1/functions/dog-breed-identifier/invoke'
AGE_PREDICTION_URL = 'https://www.nyckel.com/v1/functions/dog-age/invoke'

# Configurações do pool de conexão com o banco
DB_CONFIG = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME,
}

# Pool de conexões do banco de dados
db_pool = pooling.MySQLConnectionPool(pool_name="dog_pool", pool_size=5, **DB_CONFIG)

# Função para obter o token de acesso
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

# Função para consultar o banco de dados
def get_dog_size_from_db(breed, age_group):
    # Obtém conexão do pool
    connection = db_pool.get_connection()
    cursor = connection.cursor()

    # Consulta SQL
    query = "SELECT size FROM dogs WHERE breed = %s AND age_group = %s"
    cursor.execute(query, (breed, age_group))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    if result:
        return result[0]  # Retorna o tamanho, "Pequeno" ou "Grande"
    else:
        return None  # Caso não encontre o cachorro com essas características

@app.route('/')
def teste():
    return "Servidor Flask para identificação de raça e idade de cachorros."

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

    # Requisição para identificação da raça
    breed_response = requests.post(BREED_PREDICTION_URL, headers=headers, files=files)

    # Requisição para identificação da idade
    age_response = requests.post(AGE_PREDICTION_URL, headers=headers, files=files)

    if breed_response.status_code == 200 and age_response.status_code == 200:
        breed_result = breed_response.json()
        age_result = age_response.json()

        breed =  breed_result.get("labelName", "Raça não identificada")
        age_group = age_result.get("labelName", "Idade não identificada")

        # Chama a função para consultar o banco de dados
        dog_size = get_dog_size_from_db(breed, age_group)

        if dog_size:
            return jsonify({
                "message": "Raça, idade e tamanho identificados com sucesso!",
                "breed": breed,
                "age": age_group,
                "size": dog_size
            }), 200
        else:
            return jsonify({
                "error": f"Nenhum tamanho encontrado para a raça '{breed}' e idade '{age_group}'"
            }), 404

    else:
        error_messages = []
        if breed_response.status_code != 200:
            error_messages.append(f"Erro na identificação da raça: {breed_response.status_code} {breed_response.text}")
        if age_response.status_code != 200:
            error_messages.append(f"Erro na identificação da idade: {age_response.status_code} {age_response.text}")
        return jsonify({"error": " | ".join(error_messages)}), 500

if __name__ == '__main__':
    app.run(debug=True)
