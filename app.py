import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import requests
import mysql.connector
from mysql.connector import Error
from wtforms import Form, StringField, validators
import re

app = Flask(__name__)
app.secret_key = 'chave_secreta'
# Substitua 'SUA_CHAVE_DE_API_AQUI' pela sua chave de API real do Google Books
API_KEY = 'AIzaSyDRIxl5TD8nx01WD_LwL_1kmL2lQBQZj20'
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_DATABASE = os.getenv('DB_DATABASE', 'book_database')
DB_USER = os.getenv('DB_USER', 'book_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', '123456')


"""
Se desejar fazer o deploy da palicação recomenta-se descomentar as linhas a seguir

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')  # Define a chave secreta usando uma variável de ambiente
# Pegando a chave da API do Google Books a partir da variável de ambiente
API_KEY = os.getenv('GOOGLE_BOOKS_API_KEY', 'default_api_key')
# Pegando as informações do banco de dados a partir das variáveis de ambiente

ATENÇÃO!!!! 
É de extrema importancia para a segurança da aplicação a definição das variaveis de ambinte na plataforma escolhida para fazer o deploy

"""
@app.route('/', methods=['GET'])
def index():
    """
    Rota para a página inicial. 
    Cria um novo formulário e o passa para o template 'index.html'.
    """
    form = BarcodeForm()
    return render_template('index.html', form=form)

class BarcodeForm(Form):
    barcode = StringField('Barcode', [
        validators.DataRequired(),
        validators.Length(min=10, max=13, message='O código de barras deve ter entre 10 e 13 caracteres.'),
        validators.Regexp(r'^\d+$', message='O código de barras deve conter apenas números.')
    ])

    def validate_barcode(self, field):
        if len(field.data) not in [10, 13]:
            raise validators.ValidationError('O código de barras deve ter exatamente 10 ou 13 dígitos.')



@app.route('/manual', methods=['POST'])
def manual_entry():
    """
    Rota para entrada manual de código de barras.
    Valida o formulário e redireciona para a rota 'result' se válido.
    Caso contrário, exibe uma mensagem de erro no template 'index.html'.
    """
    form = BarcodeForm(request.form)
    if form.validate():
        barcode_number = form.barcode.data
        book_info = process_barcode(barcode_number)
        if book_info:
            save_book_info(book_info)  # Certifique-se de que essa função é chamada apenas uma vez
            return redirect(url_for('result', barcode=barcode_number))
        else:
            flash('Nenhum livro encontrado para o código de barras fornecido.', 'error')
    else:
        flash('Código de barras inválido.', 'error')
    return render_template('index.html', form=form)

    
@app.route('/result')
def result():
    """
    Rota para exibir os resultados da busca por código de barras.
    Obtém o número do código de barras da query string e chama a função 'process_barcode'.
    Renderiza o template 'result.html' com as informações do livro.
    """
    barcode_number = request.args.get('barcode')
    book_info = process_barcode(barcode_number)
    return render_template('result.html', book_info=book_info)

def process_barcode(barcode_number):
    """
    Processa o código de barras usando a API do Google Books.
    Retorna as informações do livro encontrado ou uma mensagem de erro se não encontrado.
    """
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

            # Verifique se o livro já foi adicionado
            if not is_book_in_database(barcode_number):
                save_book_info(book_info)  # Apenas salva se não estiver no banco

            return book_info
        else:
            return {"error": "Nenhum livro encontrado para o código de barras fornecido."}

    except requests.exceptions.RequestException as e:
        return {"error": f"Erro de solicitação HTTP: {str(e)}"}
    except Exception as e:
        return {"error": f"Erro ao obter informações do livro: {str(e)}"}


def is_book_in_database(barcode_number):
    """
    Verifica se um livro com o código de barras fornecido já está no banco de dados.
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_DATABASE,
            user=DB_USER,
            password=DB_PASSWORD
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = "SELECT COUNT(*) FROM livros WHERE isbn_13 = %s OR isbn_10 = %s"
            cursor.execute(query, (barcode_number, barcode_number))
            result = cursor.fetchone()
            return result['COUNT(*)'] > 0
    except mysql.connector.Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    return False

# rota para editar livros
@app.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    """
    Rota para editar informações de um livro no banco de dados.
    Obtém os dados do livro pelo ID, permite a edição e atualiza no banco de dados.
    Redireciona para a rota 'listar_livros' após a atualização.
    """
    connection = mysql.connector.connect(
        host=DB_HOST,
        database=DB_DATABASE,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM livros WHERE id = %s", (book_id,))
    book = cursor.fetchone()

    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        editora = request.form['editora']
        data_publicacao = request.form['data_publicacao']
        isbn_13 = request.form['isbn_13']
        isbn_10 = request.form['isbn_10']
        categorias = request.form['categorias']

        cursor.execute("""
            UPDATE livros
            SET titulo = %s, autor = %s, editora = %s, data_publicacao = %s, isbn_13 = %s, isbn_10 = %s, categorias = %s
            WHERE id = %s
        """, (titulo, autor, editora, data_publicacao, isbn_13, isbn_10, categorias, book_id))
        connection.commit()
        flash('Livro atualizado com sucesso!', 'success')
        return redirect(url_for('listar_livros'))

    return render_template('edit_book.html', book=book)

# rota para deletar livros
@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    """
    Rota para deletar um livro do banco de dados pelo ID.
    Realiza a exclusão do registro e redireciona para a rota 'listar_livros'.
    """
    connection = mysql.connector.connect(
        host=DB_HOST,
        database=DB_DATABASE,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = connection.cursor()
    cursor.execute("DELETE FROM livros WHERE id = %s", (book_id,))
    connection.commit()
    flash('Livro deletado com sucesso!', 'success')
    return redirect(url_for('listar_livros'))


def save_book_info(book_info):
    """
    Salva as informações do livro no banco de dados MySQL.
    Cria a tabela 'livros' se não existir e insere os dados do livro.
    """
    print("Chamando save_book_info")  # Adicione esta linha para depuração
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


@app.route('/livros', methods=['GET', 'POST'])
def listar_livros():
    """
    Rota para listar todos os livros registrados no banco de dados.
    Suporta busca, filtragem por autor e categoria, e paginacao.
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_DATABASE,
            user=DB_USER,
            password=DB_PASSWORD
        )

        cursor = connection.cursor(dictionary=True)
        
        # Adicionar busca e filtros
        search_query = request.args.get('search', '')
        filter_by_author = request.args.get('author', '')
        filter_by_category = request.args.get('category', '')
        
        # Paginação
        page = request.args.get('page', 1, type=int)
        per_page = 10 # Número de itens por página       
        offset = (page - 1) * per_page
        
        query = "SELECT * FROM livros WHERE 1=1"
        params = []

        if search_query:
            query += " AND (titulo LIKE %s OR autor LIKE %s)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        if filter_by_author:
            query += " AND autor = %s"
            params.append(filter_by_author)

        if filter_by_category:
            query += " AND categorias LIKE %s"
            params.append(f"%{filter_by_category}%")
        
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(query, params)
        livros = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM livros WHERE 1=1")
        total_livros = cursor.fetchone()['COUNT(*)']
        total_pages = (total_livros + per_page - 1) // per_page
        
        return render_template('livros.html', livros=livros, search_query=search_query, filter_by_author=filter_by_author, filter_by_category=filter_by_category, page=page, total_pages=total_pages)
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
