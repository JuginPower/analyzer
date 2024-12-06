from django.db import models

class Indiz(models.Model):

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return str(self.name)

class IndizData(models.Model):

    date = models.DateField()
    indiz = models.ForeignKey(Indiz, on_delete=models.CASCADE, related_name="data") # Was muss in related_name?
    open = models.DecimalField(max_digits=8, decimal_places=2) # Braucht es ein Namen?
    high = models.DecimalField(max_digits=8, decimal_places=2)
    low = models.DecimalField(max_digits=8, decimal_places=2)
    close = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ('date', 'indiz')  # Definiert das zusammengesetzte Primärschlüssel
        verbose_name_plural = "Indiz Data"

    def __str__(self):
        return f"{self.indiz.name} - {self.date}"
    # Brauche UniqueConstraint als pk (date, indiz)