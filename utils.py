# utils.py
# Utility functions for the RFID project

def hash_card_id(card_id):
    import hashlib
    return hashlib.sha256(card_id.encode()).hexdigest() 