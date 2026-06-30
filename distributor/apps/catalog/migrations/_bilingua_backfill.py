"""Shared raw-SQL backfill: copy each base column into its `_uk` variant.

Raw SQL avoids modeltranslation/SummernoteTextField field machinery in
historical migration models and copies exact stored bytes."""


def backfill(connection, table_fields):
    with connection.cursor() as cursor:
        for table, fields in table_fields:
            for field in fields:
                cursor.execute(
                    f"UPDATE {table} SET {field}_uk = {field} WHERE {field}_uk IS NULL"
                )
