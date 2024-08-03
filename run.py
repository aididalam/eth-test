# run.py
from transfer import Transfer
from private_key import Privatekey
import threading
import time
import traceback
from firebase_setup import initialize_firebase

def run_transfer(db):
    while True:
        try:
            trs = Transfer(db)
            trs.run()
        except Exception as e:
            print(f"Transfer encountered an error: {e}")
            traceback.print_exc()
            print("Restarting Transfer...")
            time.sleep(5)  # Wait for a few seconds before restarting

def run_privatekey(db):
    while True:
        try:
            privatekey = Privatekey(db)
            privatekey.run()
        except Exception as e:
            print(f"Privatekey encountered an error: {e}")
            traceback.print_exc()
            print("Restarting Privatekey...")
            time.sleep(5)  # Wait for a few seconds before restarting

if __name__ == "__main__":
    # Initialize Firebase and get Firestore client
    db = initialize_firebase()

    # Create threads for both classes
    transfer_thread = threading.Thread(target=run_transfer, args=(db,))
    privatekey_thread = threading.Thread(target=run_privatekey, args=(db,))

    # Start both threads
    transfer_thread.start()
    privatekey_thread.start()

    # Wait for both threads to finish
    transfer_thread.join()
    privatekey_thread.join()
