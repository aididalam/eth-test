import mysql.connector
import random
import requests
import threading
from eth_account import Account
from mnemonic import Mnemonic

Account.enable_unaudited_hdwallet_features()

# Database Configuration
db_config = {
    'host': "localhost",
    'user': "root",
    'password': "root1234",
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

# Function to check balances via API
def get_balance(addresses, api_key, blockchain):
    address_list = ",".join(addresses)
    if blockchain == "etherscan":
        url = f"https://api.etherscan.io/api?module=account&action=balancemulti&address={address_list}&tag=latest&apikey={api_key}"
    else:
        url = f"https://api.bscscan.com/api?module=account&action=balancemulti&address={address_list}&tag=latest&apikey={api_key}"

    response = requests.get(url)
    data = response.json()
    return data["result"]

# Function to save data to the database
def save_to_database(data):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    try:
        sql = "INSERT INTO addresses (address, private_key, seed_phrase, eth_balance, bsc_balance) VALUES (%s, %s, %s, %s, %s)"
        val = [(entry['public'], entry['private'], entry['seed_phrase'], entry['eth_balance'], entry['bsc_balance']) for entry in data]
        cursor.executemany(sql, val)
        connection.commit()
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

        # Generate 20 addresses
        address_data = []
        while len(address_data) < 20:
            seed_phrase = " ".join(random.choices(english_words, k=12))
            mnemonic = Mnemonic("english")
            if not mnemonic.check(seed_phrase):
                continue
            eth_account = Account.from_mnemonic(seed_phrase)
            eth_address = eth_account.address
            private_key = eth_account.key.hex()

            address_info = {
                "private": private_key,
                "public": eth_address,
                "seed_phrase": seed_phrase
            }
            address_data.append(address_info)

        eth_addresses = [data['public'] for data in address_data]
        bsc_addresses = eth_addresses.copy()

        if len(bsc_addresses) == 0:
            return

        # Check balances via API
        eth_balances = get_balance(eth_addresses, eth_api_key, "etherscan")
        bsc_balances = get_balance(bsc_addresses, bsc_api_key, "bscscan")

        # Update address_data with balances
        for i in range(len(address_data)):
            eth_balance = eth_balances[i]["balance"] if i < len(eth_balances) else "0"
            bsc_balance = bsc_balances[i]["balance"] if i < len(bsc_balances) else "0"
            address_data[i]['eth_balance'] = eth_balance
            address_data[i]['bsc_balance'] = bsc_balance


        # Filter out addresses with zero balance
        valid_data = [data for data in address_data if int(data['eth_balance']) > 0 or int(data['bsc_balance']) > 0]

        # Save to database
        save_to_database(valid_data)

    except Exception as e:
        print(f"Thread {thread_id} encountered an error: {e}")

def main(num_threads=1):
    global current_eth_api_key_index
    global current_bsc_api_key_index

    while True:
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

if __name__ == "__main__":
    current_eth_api_key_index = 0
    current_bsc_api_key_index = 0
    main(num_threads=4)
