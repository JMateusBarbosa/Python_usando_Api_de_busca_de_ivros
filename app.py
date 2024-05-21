import os
import cv2
from pyzbar.pyzbar import decode
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
import requests
import json

app = Flask(__name__)

# Substitua 'SUA_CHAVE_DE_API_AQUI' pela sua chave de API real do Google Books
API_KEY = 'AIzaSyDRIxl5TD8nx01WD_LwL_1kmL2lQBQZj20'

@app.route('/')
def index():
    return render_template('index.html')

def generate_frames():
    cap = cv2.VideoCapture(0)  # Inicialize a câmera (pode variar em sistemas diferentes)
    while True:
        success, frame = cap.read()  # Capture frame-by-frame
        if not success:
            break
        else:
            # Codifique o frame como JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # Converta frame para bytes e renderize no navegador
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/scan', methods=['POST'])
def scan():
    cap = cv2.VideoCapture(0)  # Inicialize a câmera (pode variar em sistemas diferentes)
    
    barcode_number = None
    while True:
        ret, frame = cap.read()  # Captura um quadro da câmera
        
        # Decodifique o código de barras na imagem
        barcode_number = decode_barcode(frame)

        if barcode_number:
            break

    # Libere a câmera
    cap.release()
    cv2.destroyAllWindows()

    if barcode_number:
        return redirect(url_for('result', barcode=barcode_number))
    else:
        return "Código de barras não encontrado. Tente novamente."

def decode_barcode(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    barcodes = decode(gray_image)
    for barcode in barcodes:
        barcode_data = barcode.data.decode('utf-8')
        return barcode_data
    return None

@app.route('/manual', methods=['POST'])
def manual_entry():
    barcode_number = request.form['barcode']
    return redirect(url_for('result', barcode=barcode_number))

@app.route('/result')
def result():
    barcode_number = request.args.get('barcode')
    book_info = process_barcode(barcode_number)
    return render_template('result.html', book_info=book_info)

def process_barcode(barcode_number):
    try:
        response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=isbn:{barcode_number}&key={API_KEY}')
        response.raise_for_status()  # Lança uma exceção para erros de solicitação HTTP

        response_data = response.json()

        if 'items' in response_data:
            book_data = response_data['items'][0]['volumeInfo']

            title = book_data.get('title', 'Informação não disponível')
            author = book_data.get('authors', ['Informação não disponível'])[0]
            publisher = book_data.get('publisher', 'Informação não disponível')
            published_date = book_data.get('publishedDate', 'Informação não disponível')
            
            isbn_13 = None
            isbn_10 = None
            if 'industryIdentifiers' in book_data:
                for identifier in book_data['industryIdentifiers']:
                    if identifier['type'] == 'ISBN_13':
                        isbn_13 = identifier.get('identifier', 'Informação não disponível')
                    elif identifier['type'] == 'ISBN_10':
                        isbn_10 = identifier.get('identifier', 'Informação não disponível')

            categories = book_data.get('categories', ['Informação não disponível'])[0]

            book_info = {
                'Título': title,
                'Autor': author,
                'Editora': publisher,
                'Data de Publicação': published_date,
                'ISBN-13': isbn_13,
                'ISBN-10': isbn_10,
                'Categorias': categories
            }

            with open('book_info.json', 'a', encoding='utf-8') as file:
                json.dump(book_info, file, indent=4, ensure_ascii=False)
                file.write('\n')

            return book_info
        else:
            return {"error": "Nenhum livro encontrado para o código de barras fornecido."}

    except requests.exceptions.RequestException as e:
        return {"error": f"Erro de solicitação HTTP: {str(e)}"}
    except Exception as e:
        return {"error": f"Erro ao obter informações do livro: {str(e)}"}

if __name__ == '__main__':
    app.run(debug=True)
