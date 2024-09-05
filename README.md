# Gerenciamento de Livros com Flask

## Objetivo

<p>O sistema tem como objetivo principal gerenciar informações de livros utilizando um aplicativo web desenvolvido com Flask. Ele permite aos usuários buscar e registrar livros no banco de dados através de um código de barras (ISBN), além de editar, deletar e listar os livros registrados.</p>
Funcionalidades
<ul>
  <li><strong>Busca de Livros por Código de Barras:</strong> Busca informações de livros usando a API do Google Books.</li>
  <li><strong>Formulário de Entrada Manual:</strong> Entrada e validação do código de barras.</li>
  <li><strong>Exibição de Resultados:</strong> Exibe informações detalhadas do livro.</li>
  <li><strong>Persistência de Dados:</strong> Armazena informações dos livros em um banco de dados MySQL.</li>
  <li><strong>Edição e Exclusão de Livros:</strong> Permite editar e deletar livros registrados.</li>
  <li><strong>Listagem de Livros:</strong> Lista todos os livros com suporte a busca e filtragem.</li>
  <li><strong>Feedback ao Usuário:</strong> Mensagens de sucesso e erro são exibidas para as operações realizadas.</li>
</ul>
Pré-requisitos
<ul>
  <li>Python 3.6 ou superior</li>
  <li>MySQL</li>
</ul>
Configuração e Instalação
<h3>Passo 1: Clonar o Repositório</h3>
<pre><code>
git clone https://github.com/JMateusBarbosa/Python_usando_Api_de_busca_de_livros
cd Python_usando_Api_de_busca_de_livros
</code></pre>
<h3>Passo 2: Criar e Ativar um Ambiente Virtual</h3>
<pre><code>
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
</code></pre>
<h3>Passo 3: Instalar as Dependências</h3>
<pre><code>
pip install -r requirements.txt
</code></pre>
<h3>Passo 4: Configurar Variáveis de Ambiente</h3>
<p>Crie um arquivo <code>.env</code> na raiz do projeto e adicione as seguintes variáveis de ambiente:</p>
<pre><code>
DB_HOST=localhost
DB_DATABASE=book_database
DB_USER=book_user
DB_PASSWORD=123456
API_KEY=SUA_CHAVE_DE_API_AQUI
</code></pre>
<h3>Passo 5: Configurar o Banco de Dados MySQL</h3>
<ul>
  <li>Crie um banco de dados no MySQL:
<pre><code>
CREATE DATABASE book_database;
</code></pre>
  </li>
  <li>Crie um usuário e conceda permissões:
<pre><code>
CREATE USER 'book_user'@'localhost' IDENTIFIED BY '123456';
GRANT ALL PRIVILEGES ON book_database.* TO 'book_user'@'localhost';
FLUSH PRIVILEGES;
</code></pre>
  </li>
</ul>
<h3>Passo 6: Executar o Aplicativo</h3>
<pre><code>
flask run
</code></pre>
<p>O aplicativo estará disponível em <a href="http://127.0.0.1:5000">http://127.0.0.1:5000</a>.</p>
Uso
<ol>
  <li>Acesse a página principal.</li>
  <li>Insira o código de barras (ISBN) de um livro para buscar suas informações.</li>
  <li>Veja os detalhes do livro retornado e salve-os no banco de dados.</li>
  <li>Use as opções de edição, exclusão e listagem para gerenciar os livros registrados.</li>
</ol>
Contribuição
<p>Contribuições são bem-vindas! Por favor, abra uma issue ou envie um pull request para discussões e melhorias.</p>
Licença
<p>Este projeto está licenciado sob a <a href="https://mit-license.org/" target="_blank">MIT License</a> </p>

<h3>Observações</h3>
<ul>
  <li>Certifique-se de substituir <code>SUA_CHAVE_DE_API_AQUI</code> pela sua chave de API real do Google Books.</li>
  <li>Verifique se todas as dependências necessárias estão listadas no arquivo <code>requirements.txt</code>.</li>
</ul>