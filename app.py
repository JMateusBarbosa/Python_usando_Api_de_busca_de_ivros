import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import requests
import mysql.connector
from mysql.connector import Error
from wtforms import Form, StringField, validators

app = Flask(__name__)
app.secret_key = 'chave_secreta_aqui'
# Substitua 'SUA_CHAVE_DE_API_AQUI' pela sua chave de API real do Google Books
API_KEY = 'AIzaSyDRIxl5TD8nx01WD_LwL_1kmL2lQBQZj20'
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_DATABASE = os.getenv('DB_DATABASE', 'book_database')
DB_USER = os.getenv('DB_USER', 'book_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', '123456')

class BarcodeForm(Form):
    barcode = StringField('Barcode', [validators.DataRequired(), validators.Length(min=10, max=13)])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manual', methods=['POST'])
def manual_entry():
    form = BarcodeForm(request.form)
    if form.validate():
        barcode_number = form.barcode.data
        book_info = process_barcode(barcode_number)
        if book_info:
            return redirect(url_for('result', barcode=barcode_number))
        else:
            flash('Nenhum livro encontrado para o código de barras fornecido.', 'error')
    else:
        flash('Código de barras inválido.', 'error')
    return render_template('index.html', form=form)

@app.route('/result')
def result():
    barcode_number = request.args.get('barcode')
    book_info = process_barcode(barcode_number)
    return render_template('result.html', book_info=book_info)

def process_barcode(barcode_number):
    try:
        response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=isbn:{barcode_number}&key={API_KEY}')
        response.raise_for_status()

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

            save_book_info(book_info)

            return book_info
        else:
            return {"error": "Nenhum livro encontrado para o código de barras fornecido."}

    except requests.exceptions.RequestException as e:
        return {"error": f"Erro de solicitação HTTP: {str(e)}"}
    except Exception as e:
        return {"error": f"Erro ao obter informações do livro: {str(e)}"}

def save_book_info(book_info):
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_DATABASE,
            user=DB_USER,
            password=DB_PASSWORD
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS livros (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    titulo VARCHAR(255),
                    autor VARCHAR(255),
                    editora VARCHAR(255),
                    data_publicacao VARCHAR(255),
                    isbn_13 VARCHAR(13),
                    isbn_10 VARCHAR(10),
                    categorias VARCHAR(255)
                )
            """)
            insert_query = """
                INSERT INTO livros (titulo, autor, editora, data_publicacao, isbn_13, isbn_10, categorias)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                book_info['Título'],
                book_info['Autor'],
                book_info['Editora'],
                book_info['Data de Publicação'],
                book_info['ISBN-13'],
                book_info['ISBN-10'],
                book_info['Categorias']
            ))
            connection.commit()

            # Adicionar mensagem flash
            flash('Livro registrado com sucesso!', 'success')
    except mysql.connector.Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        flash('Erro ao conectar ao banco de dados.', 'error')
    except Exception as e:
        print(f"Erro ao inserir dados no banco de dados: {e}")
        flash('Erro ao registrar o livro.', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/livros')
def listar_livros():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_DATABASE,
            user=DB_USER,
            password=DB_PASSWORD
        )

        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM livros")
            livros = cursor.fetchall()
            return render_template('livros.html', livros=livros)
    except Error as e:
        return f"Erro ao conectar ao MySQL: {e}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    if not API_KEY:
        raise ValueError("A chave de API do Google Books não está definida. Configure a variável de ambiente GOOGLE_BOOKS_API_KEY.")
    app.run(debug=True)
