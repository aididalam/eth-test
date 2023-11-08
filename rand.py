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
import eth_utils
import concurrent.futures
import telegram
from datetime import datetime
import asyncio
from telegram.constants import ParseMode


script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "english.txt")

current_bsc_api_key_index = 0
current_eth_api_key_index = 0

# Database Configuration
db_config = {
    'host': "192.168.0.100",
    'user': "aidid",
    'password': "root1234",
    'database': "eth_generator"
}



# Ethereum and BSC API Keys
eth_api_keys = [
    "DF9PQ4B2TMY842D1AXWCD4EARQ6QE2Y1QP",
    "XVB6JBW4V9J55G7ZER2BXQ13X5A9M4INPA",
    "6JH2KCY6E2EPBJIVJRY7J8W98E1KGTQVGU",
    "22MYUP9MSH7R5VSX3G92NCTFVXH8ZP2JAY",
    "SAQPI29AZABDCZYG7K4IJQ873X61N4GMG7",
    "5H7DY8TCDI4HJIAIGFGRD32IMMV8NWTQX6",
    "EKWZH6A868265IWHHCWY6VMTKCWM1XPYA5",
    "DNYMRQ3ZDAFHEDG3E7ZBBIZ2D6BP88J4V1",
    "68IVK5W6IBD3YG5XIGYZTWNV8KEER5QCME",
    "3PZ7HTE6BPH5F2Z1CQN3W3CAGFEY3TK5KX",
    "PY6EH5JMFNT226AY88MWN1CPR2DF3I3CJI",
    "D1UX8HI9NQGEE8P5JDIQAPMGPGR4IVJGHH",
]
bsc_api_keys = [
    "J4J4BNWW9M6F7AI3HYZJ39S6NB3T65M3QR",
    "Z9URM6R2UZ4CDUVTDRFPTRGN3A3YWPC1MM",
    "U2XWW6DRJ2GVIJCDWXTKV3K9SJ4FVVQF9V",
    "QQPH8BQGVJGRQYK448Z9YSS4SGYU8TQESD",
    "IPVVFTK3JQCYAJ5UQG4XCYYJRSCV83W3ZC",
    "9V6T8YH8JYDXD4FXQBB433XYK8EP3QVU6D",
    "3VHBAQYSCS5WJ7PZ4C81UK2UPCQCN72U22",
    "SWF2SHV2KXVA1T88UCU2Q7UMDESIEDV39Y",
    "5IPHZTGMBJ5BHWRYC37WUXP25J1X7XP32I",
    "QZJM7N3YJAA6TXNR7MQE62WSF3UTIKD4Y1",
    "43Y5TKATER7XAFIXEZQFZP5T64UAFYV77T",
    "IZMV74J5RCC2PNPK1T3BV8SR3AW8NUD35F",
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
        select_query = "SELECT seed FROM last_seed where id=1"

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
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        print("Last Seed: "+seed_phrase)
        update_query = "INSERT INTO last_seed (id, seed) VALUES (1, %s) ON DUPLICATE KEY UPDATE seed = %s"
        cursor.execute(update_query, (seed_phrase, seed_phrase))
        connection.commit()
        connection.close()
        time.sleep(0.5)
    except Exception as e:
        pass

def saveAddress(seed_phrase, keys_info):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        print("Last Seed: " + seed_phrase)
        update_query = "INSERT INTO gen_address (seed, public, private, address) VALUES (%s, %s, %s, %s)"  # Added a comma after %s
        cursor.execute(update_query, (seed_phrase, keys_info["public"], keys_info["private"], keys_info["address"]))
        connection.commit()
        connection.close()
        time.sleep(0.5)
        # saveLastDb(seed_phrase)
    except Exception as e:
        pass

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
    except eth_utils.exceptions.ValidationError as ve:
        pass
    except Exception as e:
        pass

async def sendTelegramMessage():
    # Define your Telegram bot token and chat ID
    bot_token = '5500299643:AAFqFy2q62ccRi3rX5i9BP91MyLoss0pXSA'
    chat_id = '1244387492'

# Create a Telegram bot object
    bot = telegram.Bot(token=bot_token)

    # Connect to the database
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    try:
        # Query the 'gen_address' table for rows where 'bnb_b' or 'eth_b' is greater than 0
        query = "SELECT public, private, bnb_b, eth_b FROM gen_address WHERE bnb_b > 0 OR eth_b > 0"
        cursor.execute(query)

        # Fetch the rows
        rows = cursor.fetchall()

        # Check if there are any rows to send
        if len(rows) > 0:
            # Get the current date and time
            current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Create the message content
            message_content = f"Date and Time: {current_datetime}\n\n"

            for row in rows:
                public, private, bnb_b, eth_b = row
                message_content += f"<b>Public:</b> {public}\n<b>BNB:</b> {bnb_b}\n<b>ETH:</b> {eth_b}\n\n"

            # Send the message to the Telegram chat
            await bot.send_message(chat_id=chat_id, text=message_content, parse_mode=ParseMode.HTML)

    except Exception as e:
        print(f"Error while sending Telegram message: {e}")

    finally:
        # Close the database connection
        cursor.close()
        connection.close()


async def main():
    if check_internet_connection():
        # Proceed with your code here
        print("Connected to the internet. Continuing with the code.")
    else:
        print("Could not establish an internet connection.")
    await sendTelegramMessage()

    # Load your word list
    with open(file_path, "r") as file:
        word_list = [word.strip() for word in file]

    # Define the number of words to combine
    num_words_to_combine = 12

    # Define the seed and positions for the first 12 words
    start_words="ability abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon"
    while True:
        seed_words = get_last_seed_from_db(db_config)
        if seed_words is not None:
            break
        time.sleep(1)
    seed_words=seed_words.split(" ")

    try:
        positions = [word_list.index(word) for word in seed_words]
    except:
        positions = [word_list.index(word) for word in start_words.split(" ")]
    
    # positions = [random.randint(0, len(word_list) - 1) for _ in range(num_words_to_combine)]
    count=0
    with concurrent.futures.ThreadPoolExecutor(700) as executor:
        while True:
            positions = [random.randint(0, len(word_list) - 1) for _ in range(num_words_to_combine)]
            # Generate a seed phrase using the current positions
            seed_phrase = " ".join(word_list[positions[i]] for i in range(num_words_to_combine))
            # generate_ethereum_keys(seed_phrase)
            background_thread = threading.Thread(target=generate_ethereum_keys, args=(seed_phrase,))
            background_thread.start()
            count=count+1
            if(count%5000==0):
                time.sleep(5)
            if(count==500000):
                await sendTelegramMessage()
                count=0

while True:
    try:
       asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}. Restarting in 60 seconds...")
        time.sleep(2)