from app import app, db, Sale, Seller, Item
from datetime import datetime, timedelta

def test_database_queries():
    with app.app_context():
        # Test: Abrufen aller Verkäufe
        print("Alle Verkäufe:")
        sales = db.session.query(
            Sale.id,
            Sale.seller_id,
            Sale.timestamp,
            db.func.sum(Sale.quantity).label('total_quantity'),
            Sale.invoice_path
        ).group_by(Sale.id, Sale.seller_id, Sale.timestamp, Sale.invoice_path).all()
        for sale in sales:
            print(f"Verkauf ID: {sale.id}, Verkäufer ID: {sale.seller_id}, Datum: {sale.timestamp}, Gesamtmenge: {sale.total_quantity}, Rechnungspfad: {sale.invoice_path}")

        # Test: Abrufen der Verkäufe der letzten 24 Stunden
        print("\nVerkäufe der letzten 24 Stunden:")
        now = datetime.now()
        start_date = now - timedelta(hours=24)
        recent_sales = db.session.query(
            Sale.id,
            Sale.seller_id,
            Sale.timestamp,
            db.func.sum(Sale.quantity).label('total_quantity'),
            Sale.invoice_path
        ).filter(Sale.timestamp >= start_date).group_by(Sale.id, Sale.seller_id, Sale.timestamp, Sale.invoice_path).all()
        for sale in recent_sales:
            print(f"Verkauf ID: {sale.id}, Verkäufer ID: {sale.seller_id}, Datum: {sale.timestamp}, Gesamtmenge: {sale.total_quantity}, Rechnungspfad: {sale.invoice_path}")

        # Test: Abrufen der Verkäufe der letzten 7 Tage
        print("\nVerkäufe der letzten 7 Tage:")
        start_date = now - timedelta(days=7)
        weekly_sales = db.session.query(
            Sale.id,
            Sale.seller_id,
            Sale.timestamp,
            db.func.sum(Sale.quantity).label('total_quantity'),
            Sale.invoice_path
        ).filter(Sale.timestamp >= start_date).group_by(Sale.id, Sale.seller_id, Sale.timestamp, Sale.invoice_path).all()
        for sale in weekly_sales:
            print(f"Verkauf ID: {sale.id}, Verkäufer ID: {sale.seller_id}, Datum: {sale.timestamp}, Gesamtmenge: {sale.total_quantity}, Rechnungspfad: {sale.invoice_path}")

        # Test: Abrufen aller Verkäufer
        print("\nAlle Verkäufer:")
        sellers = Seller.query.all()
        for seller in sellers:
            print(f"Verkäufer ID: {seller.id}, Name: {seller.first_name} {seller.last_name}")

        # Test: Abrufen aller Artikel
        print("\nAlle Artikel:")
        items = Item.query.all()
        for item in items:
            print(f"Artikel ID: {item.id}, Name: {item.name}, Preis: {item.price}, Kategorie ID: {item.category_id}")

if __name__ == '__main__':
    test_database_queries()
    