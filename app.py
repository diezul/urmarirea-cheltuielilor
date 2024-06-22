from flask import Flask, render_template, request, redirect, url_for
import requests
import json
from datetime import datetime
import os
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)

API_URL = os.environ.get("API_URL")

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    result = urlparse(DATABASE_URL)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    return psycopg2.connect(
        database=database,
        user=username,
        password=password,
        host=hostname
    )

def format_amount(value):
    if value is None:
        return '-'
    else:
        return f"{int(value)} lei" if value.is_integer() else f"{value} lei"

def format_month(month):
    try:
        return datetime.strptime(month, "%Y-%m").strftime("%B / %Y")
    except ValueError:
        return month

app.jinja_env.filters['format_amount'] = format_amount
app.jinja_env.filters['format_month'] = format_month

@app.route('/')
def index():
    expenses = requests.get(f"{API_URL}/expenses").json()
    general_expenses = [expense for expense in expenses if expense[1] in ['Chirie', 'Intretinere']]
    utility_expenses = [expense for expense in expenses if expense[1] in ['Gaz', 'Curent']]
    gas_months = list(set(expense[2] for expense in utility_expenses if expense[1] == 'Gaz' and not expense[5]))
    electric_months = list(set(expense[2] for expense in utility_expenses if expense[1] == 'Curent' and not expense[5]))
    return render_template('index.html', general_expenses=general_expenses, utility_expenses=utility_expenses, gas_months=gas_months, electric_months=electric_months)

@app.route('/add_index', methods=['POST'])
def add_index():
    category = request.form['category']
    month = request.form['month']
    index_value = request.form.get('index_value')
    amount = request.form.get('amount')
    data = {
        'category': category,
        'month': month,
        'index_value': index_value,
        'amount': amount
    }
    requests.post(f"{API_URL}/expense", json=data)
    return redirect(url_for('index'))

@app.route('/add_amount', methods=['POST'])
def add_amount():
    category = request.form['category']
    month = request.form['month']
    amount = request.form['amount']
    data = {
        'category': category,
        'month': month,
        'amount': amount
    }
    requests.post(f"{API_URL}/expense", json=data)
    return redirect(url_for('index'))

@app.route('/pay/<int:expense_id>', methods=['POST'])
def pay_expense(expense_id):
    requests.post(f"{API_URL}/expense/{expense_id}/pay")
    return redirect(url_for('index'))

@app.route('/delete/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    requests.delete(f"{API_URL}/expense/{expense_id}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)
