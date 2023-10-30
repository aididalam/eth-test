import mysql.connector
import subprocess
import time
from eth_keys import keys
from eth_hash.auto import keccak
import requests
import os
import random
from eth_account import Account
import threading
Account.enable_unaudited_hdwallet_features()

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "english.txt")

current_bsc_api_key_index = 0
current_eth_api_key_index = 0

# Database Configuration
db_config = {
    'host': "localhost",
    'user': "root",
    'password': "root1234",
    'database': "eth_generator"
}



# Ethereum and BSC API Keys
eth_api_keys = [
    "UJ78T6M7VBU2JIQC4KN5UPWGUWBIAUCKAC",
    "I6F2AI8VBIPWN4D87UG23PMN3WBN3WBKVX",
    "KXTGGRTBP4WITP635WE2CWITZE7JTF84YR",
    "D5YX5PI2WC6KDNVQ3HZ1QXM9D2RS6AQ2H2",
    "5SADIWAJG9TQN4EPSKEPUGIQI4XRWKN44C",
    "H5FPZ4Q5FDFNDNDHH4MT8P8JUFYJPVKQMB",
    "H2Z22TVPK2ZF4PEH56J3NQEST7R5K1S3JF",
    "8B2RGPHTI92NKFU13AJ98SN78W3S3K9XVN",
    "G3FDQWKU76R5MAAKXHIB8GPUIMMRRY15SX",
    "SW2GHIXK8QUBSRKSJK9FD2D4C8VPT5AIEU",
    "BF1Z7FX81MVTUK35424MZRHX4AN9T3EBXX",
    "E6SKDTI62R7JDAKP28ESUKX3WXTPFX7KVV",
]
bsc_api_keys = [
    "6H2ZST2W2M3QPVWJPXGSUHPJSGN6HJBT9N",
    "X6SNJZQ4JIS6IB4UDWJP8EG7W4BJMZ8ZVW",
    "HN4T18YC8QPWH2JU7UHPHBTPMKU74UJNF7",
    "NVIEYUPDUTXQ5CAKB59MBD9XU8BP5BENPK",
    "ZZHWZMHNCMJ7IZPXRIVTHANKKRI19HEA2I",
    "DA4F5M5P2NDMQBZ7KVRW4QCVA93GEU8A6Z",
    "M54DWTT2AP1E86I3WHT6U8FYQJ2BXEMZSQ",
    "X3JHA2IC3RS8EZ41YYEG4EP6NBRH4V22MH",
    "8FIC8RMH6Q6H627VFNKBKHEDUZA296PQKV",
    "RDV2XR3EWMX8W3TTBFDIK69PJQM48NX83J",
    "S11JWS3H14Q4GQH21KB8J2TN3SC1A3EHQM",
    "FPPKGYJKU1UCGIJWD7A2ZR7CG3E28XQ7EU",
]



def check_internet_connection():
    connected = False

    while not connected:
        try:
            # Use the ping command to check internet connectivity
            subprocess.check_output(["ping", "-c", "1", "google.com"])
            print("Internet is connected.")
            connected = True
        except subprocess.CalledProcessError:
            print("Internet is not connected. Waiting for 5 seconds...")
            time.sleep(5)

    return connected


def get_transaction_count_eth(address):
    global current_eth_api_key_index
    max_retries=5
    eth_api_key= eth_api_keys[current_eth_api_key_index]
    if current_eth_api_key_index>=len(eth_api_keys)-1:
        current_eth_api_key_index=0
    current_eth_api_key_index = current_eth_api_key_index+1
    for retry in range(max_retries):
        try:
            # Define the Etherscan API endpoint
            api_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={eth_api_key}"

            # Make a GET request to the Etherscan API
            response = requests.get(api_url)

            if response.status_code == 200:
                data = response.json()
                transaction_count = len(data['result'])
                print(transaction_count)
                return transaction_count
            else:
                print(f"Failed to retrieve data from Etherscan API (Attempt {retry + 1})")
        except requests.exceptions.RequestException as e:
            if "No internet connection" in str(e):
                check_internet_connection()
            else:
                print(f"Request failed with an error: {e}")
        time.sleep(5)

    print(f"Maximum retry attempts ({max_retries}) reached. Unable to retrieve transaction count.")
    return 0


def get_transaction_count_bsc(address):
    global current_bsc_api_key_index
    max_retries=5
    bsc_api_key= bsc_api_keys[current_bsc_api_key_index]
    if current_bsc_api_key_index>=len(bsc_api_keys)-1:
        current_bsc_api_key_index=0
    current_bsc_api_key_index = current_bsc_api_key_index+1
    for retry in range(max_retries):
        try:
            # Define the BSCscan API endpoint
            api_url = f"https://api.bscscan.com/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={bsc_api_key}"

            # Make a GET request to the BSCscan API
            response = requests.get(api_url)

            if response.status_code == 200:
                data = response.json()
                transaction_count = len(data['result'])
                print(transaction_count)
                return transaction_count
            else:
                print(f"Failed to retrieve data from BSCscan API (Attempt {retry + 1})")
            current_bsc_api_key_index = (current_bsc_api_key_index + 1) % len(bsc_api_keys)
        except requests.exceptions.RequestException as e:
            if "No internet connection" in str(e):
                check_internet_connection()
            else:
                print(f"Request failed with an error: {e}")
        time.sleep(5)

    print(f"Maximum retry attempts ({max_retries}) reached. Unable to retrieve transaction count.")
    return 0

def get_last_seed_from_db(db_config):
    try:
        # Connect to the database
        connection = mysql.connector.connect(**db_config)

        # Create a cursor to execute SQL queries
        cursor = connection.cursor()

        # Define the SQL query to select the last seed from the "last_seed" table
        select_query = "SELECT seed FROM last_seed ORDER BY id DESC LIMIT 1"

        # Execute the query
        cursor.execute(select_query)

        # Fetch the last seed
        last_seed = cursor.fetchone()

        # Close the cursor and database connection
        cursor.close()
        connection.close()

        # If a last seed is found, return it as a string, else return None
        if last_seed:
            return last_seed[0]
        else:
            return None
    except Exception as e:
        print(f"Error while getting last seed from the database: {e}")
        return None

def saveLastDb(seed_phrase):
    return
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    print("Last Seed: "+seed_phrase)
    update_query = "INSERT INTO last_seed (id, seed) VALUES (1, %s) ON DUPLICATE KEY UPDATE seed = %s"
    cursor.execute(update_query, (seed_phrase, seed_phrase))
    connection.commit()
    connection.close()
    time.sleep(0.5)

def saveAddress(seed_phrase, keys_info):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    print("Last Seed: " + seed_phrase)
    update_query = "INSERT INTO gen_address (seed, public, private, address) VALUES (%s, %s, %s, %s)"  # Added a comma after %s
    cursor.execute(update_query, (seed_phrase, keys_info["public"], keys_info["private"], keys_info["address"]))
    connection.commit()
    connection.close()
    time.sleep(0.5)
    saveLastDb(seed_phrase)

def processKey(keys_info, seed_phrase):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    eth_address = keys_info["address"]
    bsc_address = eth_address

    eth_transaction_count = get_transaction_count_eth(eth_address)
    bsc_transaction_count = get_transaction_count_bsc(bsc_address)
    transaction_types = []

    if eth_transaction_count > 0:
        transaction_types.append("eth")
    if bsc_transaction_count > 0:
        transaction_types.append("bsc")

    if transaction_types:
        # Connect to the database
        try:

            # Insert data into the "address" table for each transaction type
            for transaction_type in transaction_types:
                insert_query = "INSERT INTO address (address, private_key, public_key, type, seed, transaction_count) " \
                               "VALUES (%s, %s, %s, %s, %s, %s)"
                val = (eth_address, keys_info["private"], keys_info["public"], transaction_type, seed_phrase,
                       eth_transaction_count if transaction_type == "eth" else bsc_transaction_count)
                cursor.execute(insert_query, val)

            connection.commit()

            print(f"Data saved to the 'address' and 'last_seed' tables. Types: {', '.join(transaction_types)}")
        except Exception as error:
            print(f"Error saving data to the database: {error}")
    
    # Update the "last_seed" table with the new seed
    saveLastDb(seed_phrase)
             
def generate_ethereum_keys(seed_phrase):
    try:
        eth_account = Account.from_mnemonic(seed_phrase)
        eth_address = eth_account.address
        private_key = eth_account.key.hex()
        public_key = eth_account.address
        keys_info = {
            "private": private_key,
            "public": public_key,
            "address": eth_address
        }
        # processKey(keys_info,seed_phrase)
        saveAddress(seed_phrase,keys_info)
    except Exception as e:
        saveLastDb(seed_phrase)

    try:
        output_string = " ".join(seed_phrase.split()[::-1])
        eth_account = Account.from_mnemonic(output_string)
        eth_address = eth_account.address
        private_key = eth_account.key.hex()
        public_key = eth_account.address
        keys_info = {
            "private": private_key,
            "public": public_key,
            "address": eth_address
        }
        # processKey(keys_info,seed_phrase)
        saveAddress(output_string,keys_info)
    except Exception as e:
        pass

def main():
    if check_internet_connection():
        # Proceed with your code here
        print("Connected to the internet. Continuing with the code.")
    else:
        print("Could not establish an internet connection.")


    # Load your word list
    with open(file_path, "r") as file:
        word_list = [word.strip() for word in file]

    # Define the number of words to combine
    num_words_to_combine = 12

    # Define the seed and positions for the first 12 words
    start_words="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon"
    seed_words = get_last_seed_from_db(db_config) or start_words
    seed_words=seed_words.split(" ")

    try:
        positions = [word_list.index(word) for word in seed_words]
    except:
        positions = [word_list.index(word) for word in start_words.split(" ")]
    
    positions = [random.randint(0, len(word_list) - 1) for _ in range(num_words_to_combine)]


    while True:
        # Generate a seed phrase using the current positions
        seed_phrase = " ".join(word_list[positions[i]] for i in range(num_words_to_combine))
        seed_phrase = " ".join(word_list[positions[i]] for i in range(num_words_to_combine))
        # generate_ethereum_keys(seed_phrase)
        background_thread = threading.Thread(target=generate_ethereum_keys, args=(seed_phrase,))
        background_thread.start()
        # Update the positions for the next iteration
        positions[-1] += 1

        # Handle carry-over to the next loop
        for i in range(num_words_to_combine - 1, 0, -1):
            if positions[i] >= len(word_list):
                positions[i] = 0
                positions[i - 1] += 1

        # Check if all positions have exceeded the word list length
        if positions[0] >= len(word_list):
            break

while True:
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}. Restarting in 60 seconds...")
        time.sleep(2)