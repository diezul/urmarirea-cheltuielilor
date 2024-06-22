import os
import psycopg2
from urllib.parse import urlparse
from flask import Flask, request, jsonify, render_template
from waitress import serve

app = Flask(__name__)

# Configurarea bazei de date
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:FtJVAFZwBpjAwFGclcWfXZULZkOOoEOI@viaduct.proxy.rlwy.net:24869/railway')

def get_db_connection():
    result = urlparse(DATABASE_URL)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    return psycopg2.connect(
        database=database,
        user=username,
        password=password,
        host=hostname,
        port=port
    )

def init_db():
    result = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        database='postgres',
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    cursor.execute('SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s', ('railway',))
    exists = cursor.fetchone()
    if not exists:
        cursor.execute('CREATE DATABASE railway')
    
    cursor.close()
    conn.close()
    
    # Reconnect to the newly created database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        category TEXT NOT NULL,
        month TEXT NOT NULL,
        index_value INTEGER,
        amount REAL,
        is_paid BOOLEAN DEFAULT FALSE
    )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE category IN ('Chirie', 'Intretinere')")
    general_expenses = cursor.fetchall()
    cursor.execute("SELECT * FROM expenses WHERE category IN ('Gaz', 'Curent')")
    utility_expenses = cursor.fetchall()
    cursor.execute("SELECT DISTINCT month FROM expenses WHERE category='Gaz'")
    gas_months = cursor.fetchall()
    cursor.execute("SELECT DISTINCT month FROM expenses WHERE category='Curent'")
    electric_months = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', general_expenses=general_expenses, utility_expenses=utility_expenses, gas_months=gas_months, electric_months=electric_months)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    category = request.form['category']
    month = request.form['month']
    index_value = request.form.get('index_value')
    amount = request.form['amount']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO expenses (category, month, index_value, amount)
    VALUES (%s, %s, %s, %s)
    ''', (category, month, index_value, amount))
    conn.commit()
    cursor.close()
    conn.close()
    return 'Cheltuiala a fost adăugată!', 201

@app.route('/mark_paid/<int:expense_id>', methods=['POST'])
def mark_paid(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE expenses
    SET is_paid = TRUE
    WHERE id = %s
    ''', (expense_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return 'Cheltuiala a fost marcată ca plătită!', 200

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = %s', (expense_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return 'Cheltuiala a fost ștearsă!', 200

def run_flask():
    serve(app, host='0.0.0.0', port=8000)

if __name__ == '__main__':
    init_db()
    run_flask()
