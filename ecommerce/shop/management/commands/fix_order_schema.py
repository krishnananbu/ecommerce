from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fixes the shop_order table schema by adding missing financial fields'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            # Check if columns exist and add them if they don't
            cursor.execute("""
                DO $$
                BEGIN
                    BEGIN
                        ALTER TABLE shop_order ADD COLUMN subtotal numeric(10,2) DEFAULT 0;
                    EXCEPTION
                        WHEN duplicate_column THEN
                            RAISE NOTICE 'Column subtotal already exists';
                    END;
                    
                    BEGIN
                        ALTER TABLE shop_order ADD COLUMN shipping_cost numeric(10,2) DEFAULT 0;
                    EXCEPTION
                        WHEN duplicate_column THEN
                            RAISE NOTICE 'Column shipping_cost already exists';
                    END;
                    
                    BEGIN
                        ALTER TABLE shop_order ADD COLUMN tax numeric(10,2) DEFAULT 0;
                    EXCEPTION
                        WHEN duplicate_column THEN
                            RAISE NOTICE 'Column tax already exists';
                    END;
                    
                    BEGIN
                        ALTER TABLE shop_order ADD COLUMN total_amount numeric(10,2) DEFAULT 0;
                    EXCEPTION
                        WHEN duplicate_column THEN
                            RAISE NOTICE 'Column total_amount already exists';
                    END;
                END;
                $$;
            """)