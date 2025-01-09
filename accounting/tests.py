from decimal import Decimal
from datetime import date
from django.test import TestCase
from .models import Category, Transaction

class IndexViewTest(TestCase):
    def setUp(self):
        # Erstelle eine Test-Kategorie
        category = Category.objects.create(name="Einnahmen")

        # Erstelle Test-Transaktionen und ordne die Kategorie zu
        Transaction.objects.create(
            date=date(2024, 1, 15),
            amount=Decimal('150.00'),
            category=category  # Setze die Kategorie
        )

    def test_index_view_status_code(self):
        response = self.client.get("/accounting/")  # Passe die URL an
        self.assertEqual(response.status_code, 200)

    def test_index_view_context_data(self):
        response = self.client.get("/accounting/")  # Passe die URL an
        self.assertContains(response, "150.00")  # Prüfe, ob der Betrag enthalten ist
