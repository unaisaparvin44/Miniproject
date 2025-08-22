from django.core.management.base import BaseCommand
from bid_app.models import Member_fee

class Command(BaseCommand):
    help = 'Setup default Member_fee for user registration'

    def handle(self, *args, **options):
        try:
            # Check if Member_fee with 'Unpaid' exists
            member_fee = Member_fee.objects.filter(fee__iexact="Unpaid").first()
            
            if member_fee:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Member_fee with "Unpaid" already exists (ID: {member_fee.id})'
                    )
                )
            else:
                # Create the Member_fee
                member_fee = Member_fee.objects.create(fee="Unpaid")
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Created new Member_fee with "Unpaid" (ID: {member_fee.id})'
                    )
                )
            
            # List all Member_fee objects
            all_fees = Member_fee.objects.all()
            self.stdout.write(f'\n📋 All Member_fee objects:')
            for fee in all_fees:
                self.stdout.write(f'   - ID: {fee.id}, Fee: "{fee.fee}"')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            )
