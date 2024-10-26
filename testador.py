print("hello")

def gerar_previsoes_todos_itens():
    produtos = dao.listarprodutos(1)  # Assumindo que esta função retorna uma lista de produtos
    previsoes = {}

    for produto in produtos:
        produto_id = produto['id']
        previsao_html = gerar_previsao(produto_id)
        previsoes[produto_id] = previsao_html

    return previsoes

@app.route('/previsoes_todos', methods=['GET'])
def previsoes_todos():
    previsoes = gerar_previsoes_todos_itens()
    return render_template('previsoes_todos.html', previsoes=previsoes)
