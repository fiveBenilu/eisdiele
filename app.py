from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import asyncore

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    items = db.relationship('Item', backref='category', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    quantity = db.Column(db.Integer, nullable=False)
    invoice_path = db.Column(db.String(255), nullable=True)  # Neues Feld für den Pfad zur Rechnung

@app.route('/')
def index():
    sellers = Seller.query.all()
    return render_template('index.html', sellers=sellers)

@app.route('/login/<int:seller_id>')
def login(seller_id):
    session['seller_id'] = seller_id
    session['cart'] = []
    return redirect(url_for('sales_panel'))

@app.route('/sales_panel')
def sales_panel():
    if 'seller_id' not in session:
        return redirect(url_for('index'))
    categories = Category.query.all()
    return render_template('sales_panel.html', categories=categories)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'seller_id' not in session:
        return redirect(url_for('index'))
    item_id = request.form['item_id']
    cart = session.get('cart', [])
    cart.append({'id': item_id, 'quantity': 1})
    session['cart'] = cart
    flash('Artikel zum Warenkorb hinzugefügt', 'success')
    return redirect(url_for('sales_panel'))

@app.route('/get_cart_items')
def get_cart_items():
    cart = session.get('cart', [])
    item_ids = [item['id'] for item in cart]
    items = Item.query.filter(Item.id.in_(item_ids)).all()
    cart_items = []
    for item in items:
        for cart_item in cart:
            if cart_item['id'] == item.id:
                cart_items.append({
                    'id': item.id,
                    'name': item.name,
                    'price': item.price,
                    'quantity': cart_item['quantity']
                })
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    return jsonify({'items': cart_items, 'total_price': total_price})

@app.route('/complete_sale', methods=['POST'])
def complete_sale():
    if 'seller_id' not in session:
        return redirect(url_for('index'))
    seller_id = session['seller_id']
    seller = db.session.get(Seller, seller_id)
    seller_name = f"{seller.first_name} {seller.last_name}"
    cart = request.json.get('cart', [])
    generate_invoice = request.json.get('generate_invoice', False)
    send_email = request.json.get('send_email', False)
    email_address = request.json.get('email_address', '')
    invoice_number = None
    invoice_path = None

    if generate_invoice:
        invoice_number = generate_invoice_number()
        invoice_path = generate_invoice_pdf(cart, invoice_number, seller_name)

    for item in cart:
        sale = Sale(item_id=item['id'], seller_id=seller_id, quantity=item['quantity'], invoice_path=invoice_path)
        db.session.add(sale)
    db.session.commit()
    session.pop('seller_id', None)
    session.pop('cart', None)
    flash('Verkauf erfolgreich abgeschlossen und Verkäufer ausgeloggt', 'success')
    
    if invoice_path:
        full_invoice_path = os.path.join('static/invoices', invoice_path)
        # if send_email and email_address:
        #     send_invoice_email(email_address, full_invoice_path)
        return send_file(full_invoice_path, as_attachment=True, mimetype='application/pdf')
    return '', 204

def generate_invoice_number():
    last_sale = Sale.query.order_by(Sale.id.desc()).first()
    if last_sale:
        return last_sale.id + 1
    return 1

def generate_invoice_pdf(cart, invoice_number, seller_name):
    # Ensure the invoices directory exists
    if not os.path.exists('static/invoices'):
        os.makedirs('static/invoices')

    pdf_filename = f'invoice_{invoice_number}.pdf'
    pdf_path = os.path.join('static/invoices', pdf_filename)
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Logo
    logo_path = os.path.join('static', 'logo.png')
    c.drawImage(logo_path, 30, height - 80, width=50, height=50)

    # Invoice details
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, height - 100, f"Rechnung Nr. {invoice_number}")
    c.setFont("Helvetica", 12)
    c.drawString(30, height - 120, f"Datum: {datetime.now().strftime('%d.%m.%Y')}")
    c.drawString(30, height - 140, f"Sie wurden bedient von: {seller_name}")

    # Draw a line
    c.line(30, height - 150, width - 30, height - 150)

    # Table header
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 180, "Artikel")
    c.drawString(300, height - 180, "Menge")
    c.drawString(400, height - 180, "Preis")

    # Draw a line
    c.line(30, height - 190, width - 30, height - 190)

    # Table content
    y = height - 210
    total_price = 0
    for item in cart:
        item_details = db.session.get(Item, item['id'])
        c.setFont("Helvetica", 12)
        c.drawString(30, y, item_details.name)
        c.drawString(300, y, str(item['quantity']))
        c.drawString(400, y, f"{item_details.price * item['quantity']:.2f}€")
        total_price += item_details.price * item['quantity']
        y -= 20

    # Draw a line
    c.line(30, y + 10, width - 30, y + 10)

    # Total price with VAT
    total_price_with_vat = total_price / 1.19
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, y - 10, f"Nettopreis: {total_price_with_vat:.2f}€                          " + f" Gesamtpreis (inkl. MwSt. 19%): {total_price:.2f}€")

    # Draw a line
    c.line(30, y - 20, width - 30, y - 20)

    c.drawString(30, y - 40, f"Diese Rechnung wurde maschinell erstellt und ist ohne Unterschrift gültig!")

    c.save()
    return pdf_filename

@app.route('/logout')
def logout():
    session.pop('seller_id', None)
    session.pop('cart', None)
    return redirect(url_for('index'))

@app.route('/admin_dashboard')
def admin_dashboard():
    filter = request.args.get('filter', 'all_time')
    now = datetime.now()

    if filter == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter == 'yesterday':
        start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif filter == 'last_3_days':
        start_date = now - timedelta(days=3)
    elif filter == 'this_week':
        start_date = now - timedelta(days=now.weekday())
    elif filter == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif filter == 'last_month':
        first_day_of_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_date = (first_day_of_current_month - timedelta(days=1)).replace(day=1)
        end_date = first_day_of_current_month
    elif filter == 'this_year':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = None

    query = db.session.query(Sale)
    if start_date:
        query = query.filter(Sale.timestamp >= start_date)
    if filter == 'yesterday':
        query = query.filter(Sale.timestamp < end_date)

    total_sales = query.join(Item).with_entities(db.func.sum(Sale.quantity * Item.price)).scalar()
    
    sales_by_seller = query.join(Seller).join(Item).with_entities(Seller.first_name, Seller.last_name, db.func.sum(Sale.quantity * Item.price))\
        .group_by(Seller.id).all()
    
    sales_by_category = query.join(Item).join(Category).with_entities(Category.name, db.func.sum(Sale.quantity * Item.price))\
        .group_by(Category.id).all()
    
    items = Item.query.all()
    categories = Category.query.all()
    sellers = Seller.query.all()
    
    return render_template('admin_dashboard.html', total_sales=total_sales, sales_by_seller=sales_by_seller, sales_by_category=sales_by_category, items=items, categories=categories, sellers=sellers)

@app.route('/get_sales_data')
def get_sales_data():
    sales_data = db.session.query(db.func.strftime('%Y-%m-%d', Sale.timestamp), db.func.count(Sale.id))\
        .group_by(db.func.strftime('%Y-%m-%d', Sale.timestamp))\
        .order_by(db.func.strftime('%Y-%m-%d', Sale.timestamp)).all()
    
    labels = [data[0] for data in sales_data]
    sales = [data[1] for data in sales_data]
    
    return jsonify({'labels': labels, 'sales': sales})

@app.route('/get_hourly_sales_data')
def get_hourly_sales_data():
    sales_data = db.session.query(db.func.strftime('%H', Sale.timestamp), db.func.count(Sale.id))\
        .group_by(db.func.strftime('%H', Sale.timestamp))\
        .order_by(db.func.strftime('%H', Sale.timestamp)).all()
    
    labels = [f"{int(data[0]):02d}:00" for data in sales_data]
    sales = [data[1] for data in sales_data]
    
    return jsonify({'labels': labels, 'sales': sales})

@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    item = db.session.get(Item, item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Artikel erfolgreich gelöscht', 'success')
    else:
        flash('Artikel nicht gefunden', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_item/<int:item_id>', methods=['POST'])
def edit_item(item_id):
    data = request.get_json()
    item = db.session.get(Item, item_id)
    if item:
        item.name = data.get('name')
        item.price = data.get('price')
        item.category_id = data.get('category_id')
        db.session.commit()
        flash('Artikel erfolgreich bearbeitet', 'success')
    else:
        flash('Artikel nicht gefunden', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/add_item', methods=['POST'])
def add_item():
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    category_id = data.get('category_id')
    if not category_id:
        flash('Kategorie ist erforderlich', 'danger')
        return redirect(url_for('admin_dashboard'))
    item = Item(name=name, price=price, category_id=category_id)
    db.session.add(item)
    db.session.commit()
    flash('Artikel erfolgreich hinzugefügt', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_category/<int:category_id>')
def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if category:
        db.session.delete(category)
        db.session.commit()
        flash('Kategorie erfolgreich gelöscht', 'success')
    else:
        flash('Kategorie nicht gefunden', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_category/<int:category_id>', methods=['POST'])
def edit_category(category_id):
    data = request.get_json()
    category = db.session.get(Category, category_id)
    if category:
        category.name = data.get('name')
        db.session.commit()
        flash('Kategorie erfolgreich bearbeitet', 'success')
    else:
        flash('Kategorie nicht gefunden', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/add_category', methods=['POST'])
def add_category():
    data = request.get_json()
    name = data.get('name')
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    flash('Kategorie erfolgreich hinzugefügt', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_seller/<int:seller_id>')
def delete_seller(seller_id):
    seller = db.session.get(Seller, seller_id)
    if seller:
        db.session.delete(seller)
        db.session.commit()
        flash('Verkäufer erfolgreich gelöscht', 'success')
    else:
        flash('Verkäufer nicht gefunden', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_seller/<int:seller_id>', methods=['POST'])
def edit_seller(seller_id):
    data = request.get_json()
    seller = db.session.get(Seller, seller_id)
    if seller:
        name_parts = data.get('name').split()
        seller.first_name = name_parts[0]
        seller.last_name = name_parts[1] if len(name_parts) > 1 else ''
        db.session.commit()
        flash('Verkäufer erfolgreich bearbeitet', 'success')
    else:
        flash('Verkäufer nicht gefunden', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/add_seller', methods=['POST'])
def add_seller():
    data = request.get_json()
    name_parts = data.get('name').split()
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    seller = Seller(first_name=first_name, last_name=last_name)
    db.session.add(seller)
    db.session.commit()
    flash('Verkäufer erfolgreich hinzugefügt', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_all_sales', methods=['POST'])
def delete_all_sales():
    try:
        num_rows_deleted = db.session.query(Sale).delete()
        db.session.commit()
        flash(f'Alle Verkaufsdaten erfolgreich gelöscht ({num_rows_deleted} Einträge)', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Löschen der Verkaufsdaten: {str(e)}', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/get_history')
def get_history():
    return render_template('history.html')


@app.route('/invoice/<path:filename>')
def get_invoice(filename):
    return send_file(os.path.join('static/invoices', filename), as_attachment=True, mimetype='application/pdf')

@app.route('/get_transactions', methods=['POST'])
def get_transactions():
    data = request.get_json()
    period = data.get('period', '24h')
    now = datetime.now()

    if period == '24h':
        start_date = now - timedelta(hours=24)
    elif period == '2_days':
        start_date = now - timedelta(days=2)
    elif period == '7_days':
        start_date = now - timedelta(days=7)
    elif period == '30_days':
        start_date = now - timedelta(days=30)
    elif period == 'this_year':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        return jsonify({'error': 'Invalid period specified'}), 400

    transactions = db.session.query(Sale).filter(Sale.timestamp >= start_date).all()
    transactions_data = [{
        'sale_id': transaction.id,
        'item_id': transaction.item_id,
        'seller_id': transaction.seller_id,
        'timestamp': transaction.timestamp.strftime('%a, %d %b %Y %H:%M:%S GMT'),
        'quantity': transaction.quantity,
        'invoice_path': transaction.invoice_path.replace('static/', '') if transaction.invoice_path else None
    } for transaction in transactions]

    return jsonify({'transactions': transactions_data})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0',debug=True, port=5001)
    finally:
        print("Shutting down SMTP server...")
        asyncore.close_all()