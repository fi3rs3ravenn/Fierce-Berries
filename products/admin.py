from django.contrib import admin
from .models import Product , Profile

admin.site.register(Profile)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category')
    search_fields = ('name', 'category')

    