from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://avnadmin:AVNS_8AemcdG9D_tz31TwHxt@expenses-tracker-expenses-tracker.i.aivencloud.com:28129/defaultdb')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def format_amount(value):
    if value is None:
        return '-'
    else:
        return f"{int(value)} lei" if value.is_integer() else f"{value} lei"

def format_month(month):
    return datetime.strptime(month, "%Y-%m").strftime("%B / %Y")

app.jinja_env.filters['format_amount'] = format_amount
app.jinja_env.filters['format_month'] = format_month

def init_db():
    with get_db_connection() as conn:
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

@app.route('/')
def index():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE category IN ('Chirie', 'Internet', 'Intretinere')")
        general_expenses = cursor.fetchall()
        cursor.execute("SELECT * FROM expenses WHERE category IN ('Gaz', 'Curent')")
        utility_expenses = cursor.fetchall()
        cursor.execute("SELECT DISTINCT month FROM expenses WHERE category = 'Gaz' AND is_paid = FALSE")
        gas_months = cursor.fetchall()
        cursor.execute("SELECT DISTINCT month FROM expenses WHERE category = 'Curent' AND is_paid = FALSE")
        electric_months = cursor.fetchall()
    return render_template('index.html', general_expenses=general_expenses, utility_expenses=utility_expenses, gas_months=gas_months, electric_months=electric_months)

@app.route('/add_index', methods=['POST'])
def add_index():
    category = request.form['category']
    month = request.form['month']
    index_value = request.form.get('index_value')
    amount = request.form.get('amount')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if index_value:
            cursor.execute('''
            INSERT INTO expenses (category, month, index_value)
            VALUES (%s, %s, %s)
            ''', (category, month, index_value))
        else:
            cursor.execute('''
            INSERT INTO expenses (category, month, amount)
            VALUES (%s, %s, %s)
            ''', (category, month, amount))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/add_amount', methods=['POST'])
def add_amount():
    category = request.form['category']
    month = request.form['month']
    amount = request.form['amount']
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE expenses
        SET amount = %s
        WHERE category = %s AND month = %s AND index_value IS NOT NULL
        ''', (amount, category, month))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/pay/<int:expense_id>', methods=['POST'])
def pay_expense(expense_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE expenses
        SET is_paid = TRUE
        WHERE id = %s
        ''', (expense_id,))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = %s', (expense_id,))
        conn.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
