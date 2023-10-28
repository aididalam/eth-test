import mysql.connector
import requests
import time
import subprocess

# Define your API keys and database configuration
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


current_eth_api_key_index = 0
current_bsc_api_key_index = 0

db_config = {
    'host': "localhost",
    'user': "root",
    'password': "root1234",
    'database': "eth_generator"
}

def check_internet_connection():
    connected = False
    while not connected:
        try:
            subprocess.check_output(["ping", "-c", "1", "google.com"])
            print("Internet is connected.")
            connected = True
        except subprocess.CalledProcessError:
            print("Internet is not connected. Waiting for 5 seconds...")
            time.sleep(5)
    return connected

def fetch_addresses_from_db():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        select_query = "SELECT id, address FROM address"
        cursor.execute(select_query)
        addresses = cursor.fetchall()
        cursor.close()
        connection.close()
        return addresses
    except Exception as e:
        print(f"Error fetching addresses from the database: {e}")
        return []

def fetch_balances(addresses):
    eth_balances = {}
    bsc_balances = {}
    
    for address_id, address in addresses:
        eth_balance = fetch_eth_balance(address)
        bsc_balance = fetch_bsc_balance(address)
        eth_balances[address_id] = eth_balance
        bsc_balances[address_id] = bsc_balance
    

    return eth_balances, bsc_balances

def fetch_eth_balance(address):
    try:
        eth_api_key = get_next_eth_api_key()
        print(eth_api_key)
        api_url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={eth_api_key}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            balance_wei = int(data['result'])
            balance_eth = balance_wei / 1e18
            return balance_eth
        else:
            print(f"Failed to retrieve ETH balance for address {address}")
    except Exception as e:
        print(f"Error fetching ETH balance for address {address}: {e}")
    return None

def fetch_bsc_balance(address):
    try:
        bsc_api_key = get_next_bsc_api_key()
        api_url = f"https://api.bscscan.com/api?module=account&action=balance&address={address}&tag=latest&apikey={bsc_api_key}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            balance_wei = int(data['result'])
            balance_bnb = balance_wei / 1e18
            return balance_bnb
        else:
            print(f"Failed to retrieve BSC balance for address {address}")
    except Exception as e:
        print(f"Error fetching BSC balance for address {address}: {e}")
    return None

def get_next_eth_api_key():
    global current_eth_api_key_index
    api_key = eth_api_keys[current_eth_api_key_index]
    current_eth_api_key_index = (current_eth_api_key_index + 1) % len(eth_api_keys)
    return api_key

def get_next_bsc_api_key():
    global current_bsc_api_key_index
    api_key = bsc_api_keys[current_bsc_api_key_index]
    current_bsc_api_key_index = (current_bsc_api_key_index + 1) % len(bsc_api_keys)
    return api_key

def update_balances_in_db(address_id, eth_balance, bsc_balance):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        update_query = "UPDATE address SET eth_b = %s, bnb_b = %s WHERE id = %s"
        cursor.execute(update_query, (eth_balance, bsc_balance, address_id))
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        print(f"Error updating balances in the database: {e}")

def main():
    if check_internet_connection():
        print("Connected to the internet. Continuing with the code.")
    else:
        print("Could not establish an internet connection.")
    addresses = fetch_addresses_from_db()
    if addresses:
        eth_balances, bsc_balances = fetch_balances(addresses)
        for address_id, eth_balance in eth_balances.items():
            update_balances_in_db(address_id, eth_balance, bsc_balances[address_id])
            print(f"Updated balances for address {address_id}")
    else:
        print("No more addresses to process. Exiting.")

main()
