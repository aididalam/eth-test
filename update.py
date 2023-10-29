import mysql.connector
import requests
import time
import subprocess

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

batch_size = 20  # Number of addresses to process in each batch

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

def fetch_addresses_from_db(batch_size):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Select addresses from the gen_address table starting from the given ID
        select_query = f"SELECT address FROM gen_address where bnb_b is NUll ORDER BY seed ASC limit {batch_size}"
        cursor.execute(select_query)
        addresses = cursor.fetchall()

        cursor.close()
        connection.close()
        return addresses
    except Exception as e:
        print(f"Error fetching addresses from the database: {e}")
        return []
    
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

def fetch_eth_and_bsc_balances(addresses):
    eth_balances = {}
    bsc_balances = {}

    eth_addresses = []
    bsc_addresses = []

    for address, in addresses:
        eth_addresses.append(address)
        bsc_addresses.append(address)

    eth_api_key = get_next_eth_api_key()
    bsc_api_key = get_next_bsc_api_key()

    # Construct comma-separated address strings
    eth_addresses_str = ",".join(eth_addresses)
    bsc_addresses_str = ",".join(bsc_addresses)

    def fetch_eth_balance_with_retry():
        nonlocal eth_api_key
        max_retries = 5
        retries = 0
        while retries < max_retries:
            eth_balance_url = f"https://api.etherscan.io/api?module=account&action=balancemulti&address={eth_addresses_str}&tag=latest&apikey={eth_api_key}"
            eth_balance_response = requests.get(eth_balance_url)

            if eth_balance_response.status_code == 200:
                eth_balance_data = eth_balance_response.json()
                for data in eth_balance_data['result']:
                    address = data.get('account', '')
                    balance_wei = int(data['balance'])
                    balance_eth = balance_wei / 1e18
                    eth_balances[address] = balance_eth
                return

            print(f"Failed to fetch ETH balances with API key: {eth_api_key}")
            retries += 1
            eth_api_key = get_next_eth_api_key()
            time.sleep(5)  # Wait for 5 seconds before retrying

    def fetch_bsc_balance_with_retry():
        nonlocal bsc_api_key
        max_retries = 5
        retries = 0
        while retries < max_retries:
            bsc_balance_url = f"https://api.bscscan.com/api?module=account&action=balancemulti&address={bsc_addresses_str}&tag=latest&apikey={bsc_api_key}"
            bsc_balance_response = requests.get(bsc_balance_url)

            if bsc_balance_response.status_code == 200:
                bsc_balance_data = bsc_balance_response.json()
                for data in bsc_balance_data['result']:
                    address = data.get('account', '')
                    balance_wei = int(data['balance'])
                    balance_bnb = balance_wei / 1e18
                    bsc_balances[address] = balance_bnb
                return

            print(f"Failed to fetch BSC balances with API key: {bsc_api_key}")
            retries += 1
            bsc_api_key = get_next_bsc_api_key()
            time.sleep(5)  # Wait for 5 seconds before retrying

    fetch_eth_balance_with_retry()
    fetch_bsc_balance_with_retry()

    return eth_balances, bsc_balances

def update_balances_in_db(eth_balances, bsc_balances):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        for address, eth_balance in eth_balances.items():
            bsc_balance = bsc_balances.get(address, None)
            print("ad: "+address+" ETH"+ str(eth_balance)+" BNB: "+str(bsc_balance))
            if bsc_balance is not None:
                if eth_balance == 0 and bsc_balance == 0:
                    # Delete the record if both balances are zero
                    delete_query = "DELETE FROM gen_address WHERE address = %s"
                    cursor.execute(delete_query, (address,))
                else:
                    # Update balances for the current address in the database
                    update_query = "UPDATE gen_address SET eth_b = %s, bnb_b = %s WHERE address = %s"
                    cursor.execute(update_query, (eth_balance, bsc_balance, address))

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

    # Get the start ID from the last updated ID in the last_check table
    
    while True:
        # Fetch addresses in batches
        addresses = fetch_addresses_from_db(batch_size)
        
        if not addresses:
            print("No more addresses to process. Waiting.")
            time.sleep(5)
            continue

        eth_balances, bsc_balances = fetch_eth_and_bsc_balances(addresses)
        update_balances_in_db(eth_balances, bsc_balances)


if __name__ == "__main__":
    main()
