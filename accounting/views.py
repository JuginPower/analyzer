from django.shortcuts import render
from django.db.models import Sum, F
from .models import Transaction
from datetime import datetime

def index(request):
    # Alle Transaktionen abrufen
    transactions = Transaction.objects.all()

    # Monatsweise Gruppierung: Einnahmen, Ausgaben und Bilanz
    monthly_summary = (
        transactions
        .values('date__year', 'date__month')
        .annotate(
            total_income=Sum('amount', filter=F('amount') > 0),  # Einnahmen
            total_expense=Sum('amount', filter=F('amount') < 0),  # Ausgaben
            balance=Sum('amount')  # Bilanz
        )
        .order_by('date__year', 'date__month')
    )

    # Jahresweise Gruppierung: Gesamtbilanz
    yearly_summary = (
        transactions
        .values('date__year')
        .annotate(
            total_balance=Sum('amount')
        )
        .order_by('date__year')
    )

    context = {
        'monthly_summary': monthly_summary,
        'yearly_summary': yearly_summary,
    }

    return render(request, 'accounting/index.html', context)
