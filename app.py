from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'avicola_key_2025'

# Conexão com banco


def get_db():
    conn = sqlite3.connect('pedidos.db')
    conn.row_factory = sqlite3.Row
    return conn

# Cria tabela se não existir


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                data TEXT NOT NULL,
                status TEXT DEFAULT 'pendente',
                pago INTEGER DEFAULT 0,  -- 0 = não pago, 1 = pago
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# Página principal


@app.route('/')
def index():
    with get_db() as conn:
        pedidos = conn.execute(
            "SELECT * FROM pedidos ORDER BY data DESC").fetchall()

        # Estatísticas básicas
        total = conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        hoje = conn.execute(
            "SELECT COUNT(*) FROM pedidos WHERE data = date('now')").fetchone()[0]

        # Total de frangos pedidos
        total_frangos = conn.execute(
            "SELECT SUM(quantidade) FROM pedidos").fetchone()[0] or 0

        # Frangos hoje
        frangos_hoje = conn.execute(
            "SELECT SUM(quantidade) FROM pedidos WHERE data = date('now')").fetchone()[0] or 0

    return render_template('index.html',
                           pedidos=pedidos,
                           total=total,
                           hoje=hoje,
                           total_frangos=total_frangos,
                           frangos_hoje=frangos_hoje)

# Adicionar pedido


@app.route('/add', methods=['POST'])
def add():
    cliente = request.form['cliente'].strip()
    quantidade = request.form['quantidade']
    data = request.form['data']
    status = request.form['status']
    pago = 1 if request.form.get('pago') == 'on' else 0  # Checkbox: on = pago

    # Validação simples
    if len(cliente) < 3:
        flash('Nome muito curto', 'error')
        return redirect(url_for('index'))

    if not quantidade.isdigit() or int(quantidade) < 1:
        flash('Quantidade inválida', 'error')
        return redirect(url_for('index'))

    with get_db() as conn:
        conn.execute("""
            INSERT INTO pedidos (cliente, quantidade, data, status, pago) 
            VALUES (?, ?, ?, ?, ?)
        """, (cliente, quantidade, data, status, pago))
        conn.commit()

    flash('Pedido adicionado!', 'success')
    return redirect(url_for('index'))

# Editar pedido


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    with get_db() as conn:
        if request.method == 'POST':
            cliente = request.form['cliente']
            quantidade = request.form['quantidade']
            data = request.form['data']
            status = request.form['status']
            pago = 1 if request.form.get('pago') == 'on' else 0

            conn.execute("""
                UPDATE pedidos 
                SET cliente=?, quantidade=?, data=?, status=?, pago=?
                WHERE id=?
            """, (cliente, quantidade, data, status, pago, id))
            conn.commit()

            flash('Pedido atualizado!', 'success')
            return redirect(url_for('index'))

        pedido = conn.execute(
            "SELECT * FROM pedidos WHERE id=?", (id,)).fetchone()

    return render_template('edit.html', pedido=pedido)

# Apagar pedido


@app.route('/delete/<int:id>')
def delete(id):
    with get_db() as conn:
        conn.execute("DELETE FROM pedidos WHERE id=?", (id,))
        conn.commit()

    flash('Pedido apagado!', 'warning')
    return redirect(url_for('index'))

# Alternar status de pagamento


@app.route('/toggle_pago/<int:id>')
def toggle_pago(id):
    with get_db() as conn:
        # Verificar status atual
        pedido = conn.execute(
            "SELECT pago FROM pedidos WHERE id=?", (id,)).fetchone()
        novo_status = 0 if pedido['pago'] == 1 else 1  # Inverte o status
        conn.execute("UPDATE pedidos SET pago = ? WHERE id = ?",
                     (novo_status, id))
        conn.commit()

    flash('Status de pagamento alterado!', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
