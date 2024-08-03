from firebase_admin import credentials, firestore
import requests
import threading
from eth_account import Account
import time
import logging

class Privatekey:
    def __init__(self,db, num_threads=1):
        self.db = db
        self.eth_api_keys = self.read_api_keys_from_firestore('eth_key')
        self.bnb_api_keys = self.read_api_keys_from_firestore('bnb_key')

        self.current_eth_api_key_index = 0
        self.current_bnb_api_key_index = 0
        self.num_threads = num_threads

        self.static_start_key = "1"
        self.start_key = self.read_last_key(self.static_start_key)

    def read_api_keys_from_firestore(self, collection_name):
        api_keys = []
        docs = self.db.collection(collection_name).stream()
        for doc in docs:
            api_keys.append(doc.to_dict().get('key'))
        return api_keys

    def read_last_key(self, default_key):
        try:
            doc = self.db.collection('last_key').document('last_key_doc').get()
            if doc.exists:
                return doc.to_dict().get('key', default_key)
            else:
                return default_key
        except Exception as e:
            print(f"Error reading last key from Firestore: {e}")
            return default_key

    def write_last_key(self, key):
        try:
            self.db.collection('last_key').document('last_key_doc').set({'key': key})
        except Exception as e:
            print(f"Error writing last key to Firestore: {e}")

    def get_balance(self, addresses, api_key, blockchain):
        address_list = ",".join(addresses)
        if blockchain == "etherscan":
            url = f"https://api.etherscan.io/api?module=account&action=balancemulti&address={address_list}&tag=latest&apikey={api_key}"
        else:
            url = f"https://api.bscscan.com/api?module=account&action=balancemulti&address={address_list}&tag=latest&apikey={api_key}"

        attempts = 0
        while attempts < 3:
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                return data["result"]
            except requests.exceptions.RequestException as e:
                attempts += 1
                print(f"Attempt {attempts} failed for {blockchain}: {e}")
                time.sleep(5)

        return None

    def save_to_database(self, data):
        if not data:
            return
        
        try:
            # Create a set to track unique addresses and a list to store entries to save
            unique_addresses = set(entry['public'] for entry in data)
            addresses_to_save = []

            # Fetch existing addresses from Firestore
            if unique_addresses:
                # Query Firestore to find existing addresses
                existing_docs = self.db.collection('addresses') \
                    .where('public', 'in', list(unique_addresses)) \
                    .stream()

                # Collect existing addresses
                existing_addresses = set(doc.to_dict()['public'] for doc in existing_docs)

                # Filter out existing addresses
                addresses_to_save = [entry for entry in data if entry['public'] not in existing_addresses]

            if not addresses_to_save:
                print("No new addresses to save.")
                return

            print(f"Saving {len(addresses_to_save)} unique addresses to Firestore.")

            # Initialize Firestore batch
            batch = self.db.batch()

            # Add unique data to batch
            for entry in addresses_to_save:
                doc_ref = self.db.collection('addresses').document()
                batch.set(doc_ref, entry)

            # Commit batch to Firestore
            batch.commit()

        except Exception as e:
            print(f"Error saving to Firestore: {e}")

    def process_addresses(self, thread_id, eth_api_key, bnb_api_key, start_key):
        try:
            thread_start_key = int(start_key, 16) + (thread_id - 1) * 20
            thread_start_key = hex(thread_start_key)[2:].zfill(64)

            address_data = []
            for i in range(20):
                private_key_int = int(thread_start_key, 16) + i
                private_key_hex = hex(private_key_int)[2:].zfill(64)
                eth_account = Account.from_key(private_key_hex)
                eth_address = eth_account.address

                address_info = {
                    "private": private_key_hex,
                    "public": eth_address,
                    "seed_phrase": None
                }
                address_data.append(address_info)

            eth_addresses = [data['public'] for data in address_data]
            bnb_addresses = eth_addresses.copy()

            if len(bnb_addresses) == 0:
                return

            eth_balances = self.get_balance(eth_addresses, eth_api_key, "etherscan")
            bnb_balances = self.get_balance(bnb_addresses, bnb_api_key, "bscscan")

            if eth_balances is None and bnb_balances is None:
                return

            for i in range(len(address_data)):
                eth_balance = eth_balances[i]["balance"] if i < len(eth_balances) else "0"
                bnb_balance = bnb_balances[i]["balance"] if i < len(bnb_balances) else "0"
                address_data[i]['eth_balance'] = eth_balance
                address_data[i]['bnb_balance'] = bnb_balance

            valid_data = [data for data in address_data if int(data['eth_balance']) > 0 or int(data['bnb_balance']) > 0]

            self.save_to_database(valid_data)

        except Exception as e:
            print(f"Thread {thread_id} encountered an error: {e}")

    def run(self):
        while True:
            try:
                threads = []

                for i in range(self.num_threads):
                    eth_api_key = self.eth_api_keys[self.current_eth_api_key_index]
                    bnb_api_key = self.bnb_api_keys[self.current_bnb_api_key_index]

                    self.current_eth_api_key_index += 1
                    self.current_bnb_api_key_index += 1

                    if self.current_eth_api_key_index >= len(self.eth_api_keys):
                        self.current_eth_api_key_index = 0
                    if self.current_bnb_api_key_index >= len(self.bnb_api_keys):
                        self.current_bnb_api_key_index = 0

                    thread = threading.Thread(target=self.process_addresses, args=(i + 1, eth_api_key, bnb_api_key, self.start_key))
                    thread.start()
                    threads.append(thread)

                for thread in threads:
                    thread.join()

                start_key_int = int(self.start_key, 16)
                start_key_int += self.num_threads * 20
                self.start_key = hex(start_key_int)[2:].zfill(64)

                self.write_last_key(self.start_key)

            except Exception as e:
                logging.error(f"An error occurred: {str(e)}")
                time.sleep(60)
