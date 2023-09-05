import cv2
import barcode
from barcode import EAN13
from barcode.writer import ImageWriter
import tkinter as tk
from tkinter import ttk
import requests
import json

# Função para tratar erros e exibir mensagens de erro na interface gráfica
def show_error_message(message):
    error_window = tk.Toplevel(root)
    error_window.title("Erro")
    error_label = ttk.Label(error_window, text=message)
    error_label.pack()
    ok_button = ttk.Button(error_window, text="OK", command=error_window.destroy)
    ok_button.pack()

# Função para digitalização da câmera
def scan_camera():
    cap = cv2.VideoCapture(0)  # Inicialize a câmera (pode variar em sistemas diferentes)
    
    while True:
        ret, frame = cap.read()  # Captura um quadro da câmera
        
        # Exibe o quadro em uma janela separada (opcional, apenas para visualização)
        cv2.imshow('Câmera', frame)

        # Verifique se o usuário pressionou a tecla 'q' para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Decodifique o código de barras na imagem
        decoded_barcode = decode_barcode(frame)

        if decoded_barcode:
            # Exiba o código de barras decodificado
            print("Código de Barras Decodificado:", decoded_barcode)

            # Chame a função para processar o código de barras
            process_barcode(decoded_barcode)

    # Libere a câmera e feche a janela de visualização (opcional)
    cap.release()
    cv2.destroyAllWindows()

# Função para decodificar o código de barras na imagem
def decode_barcode(image):
    # Convertemos a imagem para tons de cinza
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Use a biblioteca barcode para decodificar o código de barras
    try:
        decoded_barcode = EAN13(barcode.decode(gray_image)[0])
        return decoded_barcode
    except Exception as e:
        print("Erro ao decodificar código de barras:", str(e))
        return None

# Função para entrada manual de código de barras
def manual_entry():
    # Crie uma janela para entrada de texto
    manual_entry_window = tk.Toplevel(root)
    manual_entry_window.title("Entrada Manual de Código de Barras")

    # Crie uma etiqueta com instruções
    entry_label = ttk.Label(manual_entry_window, text="Digite o código de barras de 13 dígitos:")
    entry_label.pack()

    # Crie uma caixa de entrada de texto
    barcode_entry = ttk.Entry(manual_entry_window)
    barcode_entry.pack()

    # Função para lidar com a submissão
    def submit():
        # Obtenha o número do código de barras inserido pelo usuário
        barcode_number = barcode_entry.get()

        # Verifique se o código de barras digitado tem 13 dígitos
        if len(barcode_number) == 13 and barcode_number.isdigit():
            # Chame a função para decodificar e processar o código de barras
            process_barcode(barcode_number)
            # Feche a janela de entrada manual
            manual_entry_window.destroy()
        else:
            # Exiba uma mensagem de erro se o código de barras for inválido
            error_label.config(text="Código de barras inválido. Insira 13 dígitos numéricos.")

    # Crie um botão para submeter
    submit_button = ttk.Button(manual_entry_window, text="Submeter", command=submit)
    submit_button.pack()

    # Crie uma etiqueta para mensagens de erro (inicialmente vazia)
    error_label = ttk.Label(manual_entry_window, text="")
    error_label.pack()




# Função para processar o código de barras
def process_barcode(barcode_number):
    try:
        # Fazer uma solicitação à API do Google Books com o código de barras
        response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=isbn:{barcode_number}&key={API_KEY}')
        response.raise_for_status()  # Lança uma exceção para erros de solicitação HTTP

        response_data = response.json()

        # Verificar se há resultados
        if 'items' in response_data:
            book_data = response_data['items'][0]['volumeInfo']

            # Extrair as informações desejadas
            title = book_data.get('title', 'Informação não disponível')
            author = book_data.get('authors', ['Informação não disponível'])[0]
            publisher = book_data.get('publisher', 'Informação não disponível')
            published_date = book_data.get('publishedDate', 'Informação não disponível')

            # Criar um dicionário com as informações do livro
            book_info = {
                'Título': title,
                'Autor': author,
                'Editora': publisher,
                'Data de Publicação': published_date
            }

            # Salvar as informações em JSON com um carimbo de data e hora único
            with open('book_info.json', 'a', encoding='utf-8') as file:
                json.dump(book_info, file, indent=4, ensure_ascii=False)
                file.write('\n')  # Adicione uma linha em branco para separar os registros

            # Exibir as informações do livro (opcional)
            print("Informações do Livro:")
            for key, value in book_info.items():
                print(f"{key}: {value}")
        else:
            print("Nenhum livro encontrado para o código de barras fornecido.")

    except requests.exceptions.RequestException as e:
        show_error_message(f"Erro de solicitação HTTP: {str(e)}")
    except Exception as e:
        show_error_message(f"Erro ao obter informações do livro: {str(e)}")

# Substitua 'SUA_CHAVE_DE_API_AQUI' pela sua chave de API real do Google Books
API_KEY = 'AIzaSyDRIxl5TD8nx01WD_LwL_1kmL2lQBQZj20'

# Crie a janela principal
root = tk.Tk()
root.title("Leitor de Código de Barras")

# Crie um botão para digitalização da câmera
scan_button = ttk.Button(root, text="Digitalizar Câmera", command=scan_camera)
scan_button.pack()

# Crie um botão para entrada manual
manual_entry_button = ttk.Button(root, text="Entrada Manual de Código de Barras", command=manual_entry)
manual_entry_button.pack()

# Execute a interface gráfica
root.mainloop()






