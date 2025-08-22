#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Auction.settings')
django.setup()

from bid_app.models import Member_fee

def check_and_create_member_fee():
    """Check if Member_fee with 'Unpaid' exists, create if not"""
    try:
        # Check if Member_fee with 'Unpaid' exists
        member_fee = Member_fee.objects.filter(fee__iexact="Unpaid").first()
        
        if member_fee:
            print(f"✅ Member_fee with 'Unpaid' already exists (ID: {member_fee.id})")
        else:
            # Create the Member_fee
            member_fee = Member_fee.objects.create(fee="Unpaid")
            print(f"✅ Created new Member_fee with 'Unpaid' (ID: {member_fee.id})")
        
        # List all Member_fee objects
        all_fees = Member_fee.objects.all()
        print(f"\n📋 All Member_fee objects:")
        for fee in all_fees:
            print(f"   - ID: {fee.id}, Fee: '{fee.fee}'")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 Checking Member_fee configuration...")
    check_and_create_member_fee()
    print("\n✨ Done!")
