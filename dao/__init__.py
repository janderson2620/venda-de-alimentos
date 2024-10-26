from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor


def conectardb():
    con = psycopg2.connect(
        host='localhost',
        database='encontreamigos',
        user='postgres',
        password='12345'
    )
    return con

def inseriruser(email, nome, senha, tipo_usuario):
    conexao = conectardb()
    cur = conexao.cursor()
    try:
        sql = f"INSERT INTO usuarios (email, nome, senha, tipo_usuario) VALUES ('{email}', '{nome}', '{senha}', '{tipo_usuario}')"
        cur.execute(sql)
    except psycopg2.IntegrityError:
        conexao.rollback()
        exito = False
    else:
        conexao.commit()
        exito = True

    conexao.close()
    return exito

def consultarUser(email):
    conexao = conectardb()
    cur = conexao.cursor()
    cur.execute("SELECT email FROM usuarios WHERE email = %s", (email,))
    usuario = cur.fetchone()
    conexao.close()
    return usuario is not None


def verificarlogin(email, senha):
    conexao = conectardb()
    cur = conexao.cursor()
    cur.execute(f"SELECT * FROM usuarios WHERE email = '{email}' AND senha = '{senha}'")
    recset = cur.fetchall()
    conexao.close()
    return recset
def obter_tipo_usuario(email):
    try:
        conexao = conectardb()
        cur = conexao.cursor()
        cur.execute("SELECT tipo_usuario FROM usuarios WHERE email = %s", (email,))
        tipo_usuario = cur.fetchone()[0]
        conexao.close()
        return tipo_usuario
    except psycopg2.Error as e:
        print("Erro ao obter tipo de usuário:", e)
        return None


def inserirproduto(nome, marca, validade, preco, qtd, path):
    conexao = conectardb()
    cur = conexao.cursor()
    try:
        sql = f"INSERT INTO produtos (nome, marca, validade, preco, qtd, path) VALUES ('{nome}', '{marca}', '{validade}',{preco}, {qtd}, '{path}')"
        cur.execute(sql)
    except psycopg2.IntegrityError:
        conexao.rollback()
        exito = False
    else:
        conexao.commit()
        exito = True

    conexao.close()
    return exito

def listarprodutos(opcao):
    conexao = conectardb()
    if opcao == 0:
        cur = conexao.cursor()
    else:
        cur = conexao.cursor(cursor_factory=RealDictCursor)
    cur.execute(f"SELECT * FROM produtos")
    recset = cur.fetchall()
    conexao.close()

    return recset

def excluirproduto(id):
    try:
        conexao = conectardb()
        cur = conexao.cursor()
        cur.execute("DELETE FROM produtos WHERE id = %s", (id,))
        conexao.commit()
        conexao.close()
        print(f"Produto com ID {id} excluído com sucesso.")
    except psycopg2.Error as e:
        print("Erro ao excluir produto:", e)


def listar_clientes():
    try:
        conexao = conectardb()
        cur = conexao.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM usuarios")
        clientes = cur.fetchall()
        conexao.close()
        return clientes
    except psycopg2.Error as e:
        print("Erro ao listar clientes:", e)
        return None


def excluir_cliente(id):
    try:
        conexao = conectardb()
        cur = conexao.cursor()
        cur.execute("DELETE FROM usuarios WHERE id = %s", (id,))
        conexao.commit()
        conexao.close()
        print(f"Cliente com ID {id} excluído com sucesso.")
    except psycopg2.Error as e:
        print("Erro ao excluir cliente:", e)


# métodos utilizados na API com java
def listarprodutos_validade(inicio, fim):
    conexao = conectardb()
    cur = conexao.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM produtos WHERE validade BETWEEN %s AND %s", (inicio, fim))
    produtos = cur.fetchall()
    conexao.close()
    return produtos


def listar_pedidos_ultima_semana():
    conexao = conectardb()
    cur = conexao.cursor(cursor_factory=RealDictCursor)
    hoje = datetime.now()
    ultima_semana = hoje + timedelta(weeks=1)
    cur.execute("SELECT * FROM produtos WHERE validade BETWEEN %s AND %s ORDER BY validade", (hoje, ultima_semana))
    pedidos = cur.fetchall()
    conexao.close()
    return pedidos


def realizar_pedido(produto_id, quantidade):
    conexao = conectardb()
    cur = conexao.cursor()
    sucesso = False
    try:
        cur.execute("SELECT qtd FROM produtos WHERE id = %s", (produto_id,))
        quantidade_disponivel = cur.fetchone()[0]

        if quantidade_disponivel >= quantidade:
            nova_quantidade = quantidade_disponivel - quantidade
            cur.execute("UPDATE produtos SET qtd = %s WHERE id = %s", (nova_quantidade, produto_id))

            cur.execute("INSERT INTO pedidos (produto_id, quantidade, data_pedido) VALUES (%s, %s, %s)",
                        (produto_id, quantidade, datetime.now()))
            conexao.commit()
            sucesso = True
        else:
            print("Quantidade solicitada não disponível")
            conexao.rollback()
    except psycopg2.Error as e:
        print("Erro ao realizar pedido:", e)
        conexao.rollback()
    conexao.close()
    return sucesso

def realizar_pedido_api(nome, quantidade):
    conexao = conectardb()
    cur = conexao.cursor()
    sucesso = False
    try:
        cur.execute("SELECT qtd FROM produtos WHERE nome = %s", (nome,))
        quantidade_disponivel = cur.fetchone()[0]

        if quantidade_disponivel >= quantidade:
            nova_quantidade = quantidade_disponivel - quantidade
            cur.execute("UPDATE produtos SET qtd = %s WHERE nome = %s", (nova_quantidade, nome))

            conexao.commit()
            sucesso = True
        else:
            print("Quantidade solicitada não disponível")
            conexao.rollback()
    except psycopg2.Error as e:
        print("Erro ao realizar pedido:", e)
        conexao.rollback()
    conexao.close()
    return buscarproduto(nome)

def buscarproduto(nome):
    conexao = conectardb()
    cur = conexao.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM produtos WHERE nome = %s", (nome,))
    produto = cur.fetchone()
    conexao.close()
    return produto

def listarclientes(opcao):
    conexao = conectardb()
    if opcao == 0:
        cur = conexao.cursor()
    else:
        cur = conexao.cursor(cursor_factory=RealDictCursor)
    cur.execute(f"select * from usuarios WHERE tipo_usuario = 'CLIENTE' ")
    recset = cur.fetchall()
    conexao.close()

    return recset

def buscar_produto_por_id(produto_id):
    conn = conectardb()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, marca, validade, preco, qtd FROM produtos WHERE id = %s", (produto_id,))
    produto = cursor.fetchone()
    conn.close()
    if produto:
        return {
            'id': produto[0],
            'nome': produto[1],
            'marca': produto[2],
            'validade': produto[3],
            'preco': produto[4],
            'qtd': produto[5]
        }
    return None

def inserir_pedido(email, id_produto, quantidade, data_pedido, valor):
    conn = conectardb()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pedidos (email, id_produto, quantidade, data_pedido, valor)
        VALUES (%s, %s, %s, %s, %s)
    """, (email, id_produto, quantidade, data_pedido, valor))
    conn.commit()
    conn.close()

def atualizar_quantidade_produto(produto_id, nova_quantidade):
    conn = conectardb()
    cursor = conn.cursor()
    cursor.execute("UPDATE produtos SET qtd = %s WHERE id = %s", (nova_quantidade, produto_id))
    conn.commit()
    conn.close()


