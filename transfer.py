import requests
import threading
from web3 import Web3
import time
from pprint import pprint

class Transfer:
    def __init__(self,db):
        self.db = db
        self.eth_api_keys, self.bsc_api_keys = self.fetch_api_keys_from_firestore()

        # Fetch settings from Firestore
        settings_doc = self.db.collection('settings').document('config').get()
        if settings_doc.exists:
            settings = settings_doc.to_dict()
            self.YOUR_DESTINATION_ADDRESS = settings['YOUR_DESTINATION_ADDRESS']
            self.ETH_GAS_GWEI = settings['ETH_GAS_GWEI']
            self.ETH_GAS_LIMIT = settings['ETH_GAS_LIMIT']
            self.BNB_GAS_GWEI = settings['BNB_GAS_GWEI']
            self.BNB_GAS_LIMIT = settings['BNB_GAS_LIMIT']
            self.INFURA_PROJECT_ID = settings['INFURA_PROJECT_ID']
        else:
            raise ValueError("Settings document not found in Firestore")

    def fetch_api_keys_from_firestore(self):
        eth_api_keys = []
        bsc_api_keys = []

        eth_key_docs = self.db.collection('eth_key').stream()
        for doc in eth_key_docs:
            eth_api_keys.append(doc.to_dict().get('key'))

        bsc_key_docs = self.db.collection('bnb_key').stream()
        for doc in bsc_key_docs:
            bsc_api_keys.append(doc.to_dict().get('key'))

        return eth_api_keys, bsc_api_keys

    def fetch_addresses_from_firestore(self):
        address_docs = self.db.collection('addresses').stream()
        addresses = []
        for doc in address_docs:
            address_data = doc.to_dict()
            addresses.append({
                'address': address_data['public'],
                'private_key': address_data['private']
            })
        return addresses

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

    def process_addresses(self, thread_id, addresses_chunk, eth_api_key, bsc_api_key):
        infura_url = f'https://mainnet.infura.io/v3/{self.INFURA_PROJECT_ID}'
        eth_web3 = Web3(Web3.HTTPProvider(infura_url))
        bsc_web3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))

        # Separate ETH and BNB addresses
        eth_addresses = [address_data['address'] for address_data in addresses_chunk]
        bsc_addresses = eth_addresses.copy()

        # Check balances via API
        eth_balances = self.get_balance(eth_addresses, eth_api_key, "etherscan")
        bsc_balances = self.get_balance(bsc_addresses, bsc_api_key, "bscscan")

        if eth_balances is None and bsc_balances is None:
            return

        # Update addresses_chunk with balances
        for i, address_data in enumerate(addresses_chunk):
            try:
                address_data['eth_balance'] = float(eth_balances[i]['balance']) / 10**18 if eth_balances else 0
            except (IndexError, KeyError):
                address_data['eth_balance'] = 0
            try:
                address_data['bsc_balance'] = float(bsc_balances[i]['balance']) / 10**18 if bsc_balances else 0
            except (IndexError, KeyError):
                address_data['bsc_balance'] = 0

        # Process each address
        for address_data in addresses_chunk:
            address = address_data['address']
            private_key = address_data['private_key']
            eth_balance = address_data['eth_balance']
            bsc_balance = address_data['bsc_balance']

            # Perform ETH transfer if balance is sufficient for gas fee
            if eth_balance > self.ETH_GAS_GWEI * self.ETH_GAS_LIMIT / 10**9:
                try:
                    nonce = eth_web3.eth.get_transaction_count(address)
                    transfer_amount = eth_web3.to_wei(eth_balance - self.ETH_GAS_GWEI * self.ETH_GAS_LIMIT / 10**9, 'ether')
                    tx = {
                        'chainId': 1,
                        'nonce': nonce,
                        'to': self.YOUR_DESTINATION_ADDRESS,
                        'value': transfer_amount,
                        'gas': self.ETH_GAS_LIMIT,
                        'gasPrice': eth_web3.to_wei(self.ETH_GAS_GWEI, 'gwei')
                    }
                    signed_tx = eth_web3.eth.account.sign_transaction(tx, private_key)
                    tx_hash = eth_web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    print(f"ETH Transfer sent, TX Hash: {tx_hash.hex()}")
                except Exception as e:
                    print(f"Error transferring ETH: {e}")

            # Perform BNB transfer if balance is sufficient for gas fee
            if bsc_balance > self.BNB_GAS_GWEI * self.BNB_GAS_LIMIT / 10**9:
                try:
                    nonce = bsc_web3.eth.get_transaction_count(address)
                    transfer_amount = bsc_web3.to_wei(bsc_balance - self.BNB_GAS_GWEI * self.BNB_GAS_LIMIT / 10**9, 'ether')
                    tx = {
                        'chainId': 56,
                        'nonce': nonce,
                        'to': self.YOUR_DESTINATION_ADDRESS,
                        'value': transfer_amount,
                        'gas': self.BNB_GAS_LIMIT,
                        'gasPrice': bsc_web3.to_wei(self.BNB_GAS_GWEI, 'gwei')
                    }
                    signed_tx = bsc_web3.eth.account.sign_transaction(tx, private_key)
                    tx_hash = bsc_web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    print(f"BNB Transfer sent, TX Hash: {tx_hash.hex()}")
                except Exception as e:
                    print(f"Error transferring BNB: {e}")

    def run(self):
        while True:
            try:
                addresses = self.fetch_addresses_from_firestore()
                num_chunks = (len(addresses) + 19) // 20  # Number of 20-address chunks
                threads = []

                for i in range(num_chunks):
                    chunk_start = i * 20
                    chunk_end = (i + 1) * 20
                    addresses_chunk = addresses[chunk_start:chunk_end]

                    if not addresses_chunk:
                        continue

                    eth_api_key = self.eth_api_keys[i % len(self.eth_api_keys)]
                    bsc_api_key = self.bsc_api_keys[i % len(self.bsc_api_keys)]

                    thread = threading.Thread(target=self.process_addresses, args=(i + 1, addresses_chunk, eth_api_key, bsc_api_key))
                    thread.start()
                    threads.append(thread)

                for thread in threads:
                    thread.join()

            except Exception as e:
                print(f"An error occurred: {e}")
                # Optionally, sleep for some time before restarting
                time.sleep(60)
