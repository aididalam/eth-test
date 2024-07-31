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
last_key_file_path = "last_key.txt"

def read_api_keys(file_path):
    with open(file_path, "r") as file:
        api_keys = [line.strip() for line in file if line.strip()]
    return api_keys

eth_api_keys = read_api_keys(eth_file_path)
bsc_api_keys = read_api_keys(bsc_file_path)

# Function to read the last key from file
def read_last_key(file_path, default_key):
    try:
        with open(file_path, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return default_key

# Function to write the last key to file
def write_last_key(file_path, key):
    with open(file_path, "w") as file:
        file.write(key)

# Function to check balances via API with retries
def get_balance(addresses, api_key, blockchain):
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
            pprint(data["result"])
            print("\n")
            return data["result"]
        except requests.exceptions.RequestException as e:
            attempts += 1
            print(f"Attempt {attempts} failed for {blockchain}: {e}")
            time.sleep(5)
    
    return None
# Function to save data to the database
def save_to_database(data):
    if len(data) > 0:
        print(data)
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
def process_addresses(thread_id, eth_api_key, bsc_api_key, start_key):
    try:
        # Calculate the unique start key for this thread
        thread_start_key = int(start_key, 16) + (thread_id - 1) * 20
        thread_start_key = hex(thread_start_key)[2:].zfill(64)  # Ensure 64 characters

        address_data = []
        for i in range(20):
            private_key_int = int(thread_start_key, 16) + i
            private_key_hex = hex(private_key_int)[2:].zfill(64)  # Ensure 64 characters
            eth_account = Account.from_key(private_key_hex)
            eth_address = eth_account.address

            address_info = {
                "private": private_key_hex,
                "public": eth_address,
                "seed_phrase": None  # No seed phrase as we're directly using private keys
            }
            address_data.append(address_info)

        eth_addresses = [data['public'] for data in address_data]
        bsc_addresses = eth_addresses.copy()

        if len(bsc_addresses) == 0:
            return

        # Check balances via API
        eth_balances = get_balance(eth_addresses, eth_api_key, "etherscan")
        bsc_balances = get_balance(bsc_addresses, bsc_api_key, "bscscan")
        
        if eth_balances is None and bsc_balances is None:
            return

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

    # Static start key
    static_start_key = "0xe7c34c963ff87ecd8b7b7f5993da1ee6cc0b5a96633efd6c127f3df76dea1ea4"
    
    # Read last key from file or use static value
    start_key = read_last_key(last_key_file_path, static_start_key)

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

                thread = threading.Thread(target=process_addresses, args=(i + 1, eth_api_key, bsc_api_key, start_key))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

            # Update start_key
            start_key_int = int(start_key, 16)
            start_key_int += num_threads * 20
            start_key = hex(start_key_int)[2:].zfill(64)  # Ensure 64 characters

            # Save the updated start key
            write_last_key(last_key_file_path, start_key)

        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            # Optionally, sleep for some time before restarting
            time.sleep(60)

if __name__ == "__main__":
    current_eth_api_key_index = 0
    current_bsc_api_key_index = 0
    main(num_threads=120)
