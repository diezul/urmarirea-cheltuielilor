import os
import psycopg2
from urllib.parse import urlparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request, jsonify
import threading
from waitress import serve

# Configurarea botului
TOKEN = os.getenv('TOKEN')
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:FtJVAFZwBpjAwFGclcWfXZULZkOOoEOI@viaduct.proxy.rlwy.net:24869/railway')

app = Flask(__name__)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Bine ai venit! Folosește comenzi pentru a interacționa cu botul. /help pentru ajutor.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('/add - Adaugă o cheltuială\n/list - Listează cheltuielile\n/pay - Marchează o cheltuială ca plătită\n/delete - Șterge o cheltuială')

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('Folosește /add <categorie> <luna> <suma>')
        return
    category = args[0]
    month = args[1]
    amount = float(args[2])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO expenses (category, month, amount)
    VALUES (%s, %s, %s)
    ''', (category, month, amount))
    conn.commit()
    cursor.close()
    conn.close()
    await update.message.reply_text('Cheltuiala a fost adăugată!')

async def list_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    response = ""
    for expense in expenses:
        response += f"ID: {expense[0]}, Categorie: {expense[1]}, Luna: {expense[2]}, Suma: {expense[4]}, Plătit: {'Da' if expense[5] else 'Nu'}\n"
    cursor.close()
    conn.close()
    await update.message.reply_text(response)

async def pay_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('Folosește /pay <ID>')
        return
    expense_id = int(args[0])
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
    await update.message.reply_text('Cheltuiala a fost marcată ca plătită!')

async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('Folosește /delete <ID>')
        return
    expense_id = int(args[0])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = %s', (expense_id,))
    conn.commit()
    cursor.close()
    conn.close()
    await update.message.reply_text('Cheltuiala a fost ștearsă!')

# Flask API Routes

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(expenses)

@app.route('/api/expense', methods=['POST'])
def add_expense_via_api():
    data = request.json
    category = data.get('category')
    month = data.get('month')
    index_value = data.get('index_value')
    amount = data.get('amount')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO expenses (category, month, index_value, amount)
    VALUES (%s, %s, %s, %s)
    ''', (category, month, index_value, amount))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/expense/<int:expense_id>/pay', methods=['POST'])
def pay_expense_via_api(expense_id):
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
    return jsonify({'status': 'success'})

@app.route('/api/expense/<int:expense_id>', methods=['DELETE'])
def delete_expense_via_api(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = %s', (expense_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success'})

def run_flask():
    serve(app, host='0.0.0.0', port=5001)

def main():
    init_db()
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_expense))
    application.add_handler(CommandHandler("list", list_expenses))
    application.add_handler(CommandHandler("pay", pay_expense))
    application.add_handler(CommandHandler("delete", delete_expense))

    application.run_polling()

if __name__ == '__main__':
    main()
