import os
from datetime import datetime
from functools import wraps
from flask import *
from werkzeug.utils import secure_filename
import dao
from os.path import join, dirname, realpath
from flask import Flask, render_template
import pandas as pd

from matplotlib import pyplot as plt
from sklearn.linear_model import LinearRegression
import mpld3

app = Flask(__name__)
app.secret_key = '1715773967|9a2bd9bd187d'
app.config['UPLOAD_FOLDER'] = join(dirname(realpath(__file__)), 'static/imagens/')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/cadastrarusuario', methods=['GET', 'POST'])
def cadastrarUser():
    if request.method == 'GET':
        return render_template('cadastraruser.html')
    elif request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        tipo_cliente = request.form.get('perfil')

        if dao.inseriruser(email, nome, senha, tipo_cliente):
            texto = 'Usuário cadastrado com sucesso'
            return render_template('index.html', msg=texto)
        else:
            texto = 'Usuário já cadastrado. Tente novamente'
            return render_template('index.html', msg=texto)


@app.route('/login', methods=['GET', 'POST'])
def verificar_login():
    if request.method == 'GET':
        return render_template('pagelogin.html')
    elif request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        usuario = dao.verificarlogin(email, senha)

        if usuario:

            session['email'] = email

            tipo_usuario = dao.obter_tipo_usuario(email)

            if tipo_usuario == 'ADM':
                return render_template('home_adm.html', email=email)
            elif tipo_usuario == 'CLIENTE':
                produtos = dao.listarprodutos(1)
                return render_template('home_cliente.html', email=email, produtos=produtos)
        msg = 'Login ou senha incorretos.'
        return render_template('pagelogin.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('email', None)
    res = make_response("Cookie Removido")
    res.set_cookie('email', '', max_age=0)

    return render_template('index.html')


@app.route('/listarprodutos', methods=['GET'])
def listar_produtos():
    email = session.get('email')
    tipo_usuario = dao.obter_tipo_usuario(email)
    if email:
        produtos = dao.listarprodutos(1)
        return render_template('listarprodutos.html', produtos=produtos, meuemail=email, tipo_usuario=tipo_usuario, year=2024)
    else:
        return render_template('pagelogin.html')


@app.route('/excluir_produto/<int:id>', methods=['POST'])
def excluir_produto(id):
    email = session.get('email')
    tipo_usuario = dao.obter_tipo_usuario(email)
    if tipo_usuario == 'ADM':
        dao.excluirproduto(id)
    return render_template('listarprodutos.html')



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('email') is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/cadastrarproduto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    if request.method == 'GET':
        return render_template('cadastrarproduto.html')


    if request.method == 'GET':
        return render_template('cadastrarproduto.html')
    elif request.method == 'POST':
        nome = request.form.get('nome')
        marca = request.form.get('marca')
        validade = request.form.get('validade')
        try:
            preco = float(request.form.get('preco'))
            qtd = int(request.form.get('qtd'))
        except ValueError:
            texto = 'Erro: Preço e Quantidade devem ser números.'
            return render_template('cadastrarproduto.html', msg=texto)

        f = request.files['file']
        filename = secure_filename(f.filename)
        path = os.path.join('static', 'imagens', filename)

        if dao.inserirproduto(nome, marca, validade, preco, qtd, path):
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            texto = 'Produto cadastrado com sucesso'
            return render_template('cadastrarproduto.html', msg=texto)


@app.route('/listarprodutos/externo', methods=['GET'])
def listar_produtos_ext():
    email = session.get('email')
    if session.get(email) != None:
        result = dao.listarprodutos(1)
        return jsonify(result).json
    else:
        resp = make_response('necessário fazer login')
        resp.status_code = 511
        return resp

@app.route('/listarprodutos/externoSemlogin', methods=['GET'])
def listar_produtos_ext_semlogin():

    result = dao.listarprodutos(1)
    return jsonify(result).json



@app.route('/listarclientes', methods=['GET'])
def listar_clientes():
    usuarios = dao.listarclientes(1)

    return render_template('listar_clientes.html', usuarios=usuarios)



@app.route('/excluir_cliente/<int:id>', methods=['POST'])
def excluir_cliente(id):
    if request.method == 'POST':
        dao.excluirclientes(id)
        return redirect(url_for('listar_clientes'))

@app.route('/home_adm')
def home_adm():
    return render_template('home_adm.html')

@app.route('/fazerpedido')
def fazer_pedido():
    produtos = dao.listarprodutos(1)
    return render_template('fazerpedido.html', produtos=produtos)


@app.route('/processar_pedido', methods=['POST'])
def processar_pedido():
    if request.method == 'POST':
        selected_quantities = {}
        errors = []
        email = session.get('email')

        for key, value in request.form.items():
            if key.startswith('quantidade_'):
                produto_id = key.split('_')[1]
                if value.strip():
                    try:
                        selected_quantity = int(value)
                        if selected_quantity < 0:
                            errors.append(f'Quantidade inválida para o produto ID: {produto_id}. Deve ser um número positivo.')
                        else:
                            selected_quantities[produto_id] = selected_quantity
                    except ValueError:
                        errors.append(f'Quantidade inválida para o produto ID: {produto_id}. Deve ser um número inteiro.')
                else:
                    errors.append(f'Quantidade não pode estar vazia para o produto ID: {produto_id}.')

        if errors:
            produtos = dao.listarprodutos(1)
            return render_template('fazerpedido.html', produtos=produtos, msg=' '.join(errors))

        data_pedido = datetime.now()

        for produto_id, selected_quantity in selected_quantities.items():
            produto = dao.buscar_produto_por_id(produto_id)
            if produto:
                valor_total = produto['preco'] * selected_quantity

                dao.inserir_pedido(email, produto['id'], selected_quantity, data_pedido, valor_total)

                dao.atualizar_quantidade_produto(produto['id'], produto['qtd'] - selected_quantity)

        return redirect(url_for('fazer_pedido'))

    return redirect(url_for('fazer_pedido'))


# Funções para carregar dados do banco de dados
def carregar_dados(id_produto):
    try:
        conn = dao.conectardb()
        query = """
            SELECT EXTRACT(MONTH FROM data_pedido) AS mes, SUM(valor) AS valor
            FROM pedidos
            WHERE id_produto = %s
            GROUP BY EXTRACT(MONTH FROM data_pedido)
            ORDER BY mes
        """
        df = pd.read_sql(query, conn, params=(id_produto,))
        print("Dados carregados:")
        print(df)
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        df = pd.DataFrame()
    finally:
        if conn:
            conn.close()
    return df

# Função para gerar previsão
def gerar_previsao(produto_id):
    df = carregar_dados(produto_id)
    print(df)
    if df.empty:
        return "<p>Nenhum dado disponível para o produto especificado.</p>"

    df['mes'] = df['mes'].astype(int)
    y = df['valor'].values


    x = pd.DataFrame(pd.Series(range(1, len(y) + 1)), columns=['mes'])
    xFuturo = pd.DataFrame(pd.Series(range(1, len(y) + 13)), columns=['mes'])

    reg_model = LinearRegression().fit(x, y)
    y_pred = reg_model.predict(xFuturo)

    meses_do_ano = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    plt.figure(figsize=(12, 7))
    plt.plot(x['mes'], y, 'o', label='Dados históricos')
    plt.plot(xFuturo['mes'], y_pred, 'b', label='Previsões futuras')
    plt.xlabel('Meses')

    plt.xticks(ticks=range(1, 13), labels=meses_do_ano)
    plt.ylabel('Valor de Compras')
    plt.title(f'Previsão de Compras para Produto {produto_id}')
    plt.legend()
    plt.grid(True)

    fig = plt.gcf()
    graph_html = mpld3.fig_to_html(fig)
    #plt.show()
    plt.close()
    print("HTML do gráfico:")
    print(graph_html)

    return graph_html

@app.route('/previsao/<int:produto_id>',methods=['POST'])
def previsao(produto_id):
    graph_html = gerar_previsao(produto_id)
    produtos = dao.listarprodutos(1)
    return render_template('previsao.html', produto_id=produto_id, produtos=produtos,graph_html=graph_html)

@app.route('/test')
def test():
    test_html = "<p>Test HTML</p>"
    return render_template('previsao.html', id_produto=123, graph_html=test_html)


@app.route('/test_grafico')
def test_grafico():
    x = [1, 2, 3, 4, 5]
    y = [2, 3, 5, 7, 11]

    plt.figure(figsize=(10, 6))
    plt.plot(x, y, 'o-', label='Dados de teste')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Gráfico de Teste')
    plt.legend()
    plt.grid(True)

    fig = plt.gcf()
    graph_html = mpld3.fig_to_html(fig)
    plt.close()

    return render_template('previsao.html', produto_id='teste', graph_html=graph_html)

def carregar_dados_todos_produtos():
    try:
        conn = dao.conectardb()
        query = """
            SELECT id_produto, EXTRACT(MONTH FROM data_pedido) AS mes, SUM(valor) AS valor
            FROM pedidos
            GROUP BY id_produto, EXTRACT(MONTH FROM data_pedido)
            ORDER BY id_produto, mes
        """
        df = pd.read_sql(query, conn)
        print("Dados carregados:")
        print(df)
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        df = pd.DataFrame()
    finally:
        if conn:
            conn.close()
    return df

def gerar_previsao_todos_produtos():
    df = carregar_dados_todos_produtos()
    if df.empty:
        return "<p>Nenhum dado disponível.</p>"

    meses_do_ano = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    plt.figure(figsize=(12, 7))

    for produto_id in df['id_produto'].unique():
        df_produto = df[df['id_produto'] == produto_id]
        df_produto['mes'] = df_produto['mes'].astype(int)
        y = df_produto['valor'].values

        x = pd.DataFrame(pd.Series(range(1, len(y) + 1)), columns=['mes'])
        xFuturo = pd.DataFrame(pd.Series(range(1, 13)), columns=['mes'])

        reg_model = LinearRegression().fit(x, y)
        y_pred = reg_model.predict(xFuturo)

        plt.plot(x['mes'], y, 'o', label=f'Dados históricos - Produto {produto_id}')
        plt.plot(xFuturo['mes'], y_pred, label=f'Previsões futuras - Produto {produto_id}')

    plt.xlabel('Meses')
    plt.xticks(ticks=range(1, 13), labels=meses_do_ano)
    plt.ylabel('Valor de Compras')
    plt.title('Previsão de Compras para Todos os Produtos')
    plt.legend()
    plt.grid(True)

    fig = plt.gcf()
    graph_html = mpld3.fig_to_html(fig)
    plt.close()
    print("HTML do gráfico:")
    print(graph_html)

    return graph_html

@app.route('/previsao_todos')
def previsao_todos():
    graph_html = gerar_previsao_todos_produtos()
    produtos = dao.listarprodutos(1)
    return render_template('previsao_todos.html', produtos=produtos, graph_html=graph_html)

if __name__ == '__main__':
    app.run(debug=True)