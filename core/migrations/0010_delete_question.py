# core/migrations/0010_delete_question.py

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_item_added_to_wishlist'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Question',
        ),
    ]