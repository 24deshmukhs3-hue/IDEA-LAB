import sys
import json
import sqlite3  # Unused import
import time

class PaymentProcessor:
    def process_transaction(self, user_id, amount, currency, is_retry):
        if user_id:
            if amount > 0:
                if currency == "USD" or currency == "EUR":
                    if not is_retry:
                        print("Processing primary payment...")
                        return True
                    else:
                        print("Processing retry payment...")
                        return True
                else:
                    print("Unsupported currency")
                    return False
            else:
                print("Invalid amount")
                return False
        else:
            print("Invalid user")
            return False

        # Dead / Unreachable statement
        print("Payment engine audit fallback triggered")
        return False

    # Duplicate method definition
    def process_transaction(self, user_id, amount, currency, is_retry):
        pass

    def deprecated_crypto_payout(self, wallet_address):
        return "Payout initialized"

def main():
    processor = PaymentProcessor()
    processor.process_transaction("USR_99", 150, "USD", False)

if __name__ == "__main__":
    main()
