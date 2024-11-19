from app import app, db, Seller, Category, Item

with app.app_context():
    # Erstellen Sie die Datenbank und die Tabellen
    db.create_all()

    # Testdaten hinzufügen
    # Mitarbeiter
    seller = Seller(first_name='Bennet', last_name='Griese')
    db.session.add(seller)

    # Kategorien
    categories = [
        Category(name='Eisbecher'),
        Category(name='Getränke'),
        Category(name='Kaffee')
    ]

    for category in categories:
        db.session.add(category)

    db.session.commit()

    # Artikel hinzufügen
    items = [
        Item(name='Schokoladeneis', price=2.50, category_id=Category.query.filter_by(name='Eisbecher').first().id),
        Item(name='Vanilleeis', price=2.00, category_id=Category.query.filter_by(name='Eisbecher').first().id),
        Item(name='Erdbeereis', price=2.50, category_id=Category.query.filter_by(name='Eisbecher').first().id),
        Item(name='Cola', price=1.50, category_id=Category.query.filter_by(name='Getränke').first().id),
        Item(name='Wasser', price=1.00, category_id=Category.query.filter_by(name='Getränke').first().id),
        Item(name='Orangensaft', price=2.00, category_id=Category.query.filter_by(name='Getränke').first().id),
        Item(name='Espresso', price=1.80, category_id=Category.query.filter_by(name='Kaffee').first().id),
        Item(name='Cappuccino', price=2.50, category_id=Category.query.filter_by(name='Kaffee').first().id),
        Item(name='Latte Macchiato', price=2.80, category_id=Category.query.filter_by(name='Kaffee').first().id)
    ]

    for item in items:
        db.session.add(item)

    # Änderungen speichern
    db.session.commit()

    print("Testdaten wurden erfolgreich hinzugefügt.")