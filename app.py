from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import json

app = Flask(__name__)

# Substitua 'SUA_CHAVE_DE_API_AQUI' pela sua chave de API real do Google Books
API_KEY = 'AIzaSyDRIxl5TD8nx01WD_LwL_1kmL2lQBQZj20'

@app.route('/')
def index():
    return render_template('index.html')

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
