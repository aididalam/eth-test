import mysql.connector
import random
import requests
import threading
from eth_account import Account
from mnemonic import Mnemonic
import time
import logging
from pprint import pprint

Account.enable_unaudited_hdwallet_features()

# Database Configuration
db_config = {
    'host': "localhost",
    'user': "aidid",
    'password': "aidid",
    'database': "eth_generator"
}

eth_file_path = "eth_api.txt"
bsc_file_path = "bsc_api.txt"

def read_api_keys(file_path):
    with open(file_path, "r") as file:
        api_keys = [line.strip() for line in file if line.strip()]
    return api_keys


eth_api_keys = read_api_keys(eth_file_path)
bsc_api_keys = read_api_keys(bsc_file_path)

# English word list file path
file_path = "english.txt"


def get_transaction_count(address, api_key, blockchain):
    if blockchain == "etherscan":
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"
    else:
        url = f"https://api.bscscan.com/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"

    attempts = 0
    while attempts < 3:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data["status"] == "1":
                return len(data["result"])
            else:
                return 0
        except requests.exceptions.RequestException as e:
            attempts += 1
            print(f"Attempt {attempts} failed for {blockchain}: {e}")
            time.sleep(5)
    
    return None

# Function to save data to the database
def save_to_database(data):
    if data:
        print(data)
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    try:
        # Check if address already exists in the database
        check_sql = "SELECT COUNT(*) FROM addresses WHERE address = %s"
        cursor.execute(check_sql, (data['public'],))
        result = cursor.fetchone()
        
        if result[0] == 0:  # Address does not exist
            sql = "INSERT INTO addresses (address, private_key, seed_phrase, eth_tx_count, bsc_tx_count) VALUES (%s, %s, %s, %s, %s)"
            val = (data['public'], data['private'], data['seed_phrase'], data['eth_tx_count'], data['bsc_tx_count'])
            cursor.execute(sql, val)
            connection.commit()
        else:
            print("Address already exists in the database.")
    except mysql.connector.Error as e:
        print(f"Error saving to database: {e}")
    finally:
        cursor.close()
        connection.close()
# Function to generate addresses and check balances
def process_addresses(thread_id, eth_api_key, bsc_api_key):
    try:
        # Load English word list
        with open(file_path, "r") as file:
            english_words = [word.strip() for word in file]

        # Generate 1 address
        seed_phrase = " ".join(random.sample(english_words, 12))
        mnemonic = Mnemonic("english")
        while not mnemonic.check(seed_phrase):
            seed_phrase = " ".join(random.sample(english_words, 12))
        print(seed_phrase)
            
        eth_account = Account.from_mnemonic(seed_phrase)
        eth_address = eth_account.address
        private_key = eth_account.key.hex()

        address_info = {
            "private": private_key,
            "public": eth_address,
            "seed_phrase": seed_phrase
        }
        
        # Check transaction count via API
        eth_tx_count = get_transaction_count(eth_address, eth_api_key, "etherscan")
        bsc_tx_count = get_transaction_count(eth_address, bsc_api_key, "bscscan")
        
        if eth_tx_count is None and bsc_tx_count is None:
            return

        # Update address_info with transaction counts
        address_info['eth_tx_count'] = eth_tx_count if eth_tx_count is not None else 0
        address_info['bsc_tx_count'] = bsc_tx_count if bsc_tx_count is not None else 0

        # Save to database
        if address_info['eth_tx_count'] > 0 or address_info['bsc_tx_count'] > 0:
            save_to_database(address_info)

    except Exception as e:
        print(f"Thread {thread_id} encountered an error: {e}")
def main(num_threads=1):
    global current_eth_api_key_index
    global current_bsc_api_key_index

    while True:
        try:
            threads = []

            for i in range(num_threads):
                eth_api_key = eth_api_keys[current_eth_api_key_index]
                bsc_api_key = bsc_api_keys[current_bsc_api_key_index]
                
                # Update indices for circular key usage
                current_eth_api_key_index += 1
                current_bsc_api_key_index += 1

                if current_eth_api_key_index >= len(eth_api_keys):
                    current_eth_api_key_index = 0
                if current_bsc_api_key_index >= len(bsc_api_keys):
                    current_bsc_api_key_index = 0

                thread = threading.Thread(target=process_addresses, args=(i + 1, eth_api_key, bsc_api_key))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            # Optionally, sleep for some time before restarting
            time.sleep(60)

if __name__ == "__main__":
    current_eth_api_key_index = 0
    current_bsc_api_key_index = 0
    main(num_threads=240)
