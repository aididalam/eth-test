import mysql.connector
import requests
import time
import subprocess

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
        select_query = f"SELECT address FROM gen_address where bnb_b is NUll  ORDER BY seed ASC limit {batch_size}"
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
        max_retries = 2
        retries = 0
        while retries < max_retries:
            eth_balance_url = f"https://api.etherscan.io/api?module=account&action=balancemulti&address={eth_addresses_str}&tag=latest&apikey={eth_api_key}"
            eth_balance_response = requests.get(eth_balance_url)

            if eth_balance_response.status_code == 200:
                try:
                    eth_balance_data = eth_balance_response.json()
                    for data in eth_balance_data['result']:
                        address = data['account']
                        balance_wei = int(data['balance'])
                        balance_eth = balance_wei / 1e18
                        eth_balances[address] = balance_eth
                    return
                except Exception as e:
                    print(f"Error processing")


            print(f"Failed to fetch ETH balances with API key: {eth_api_key}")
            retries += 1
            eth_api_key = get_next_eth_api_key()
            time.sleep(5)  # Wait for 5 seconds before retrying

    def fetch_bsc_balance_with_retry():
        nonlocal bsc_api_key
        max_retries = 2
        retries = 0
        while retries < max_retries:
            bsc_balance_url = f"https://api.bscscan.com/api?module=account&action=balancemulti&address={bsc_addresses_str}&tag=latest&apikey={bsc_api_key}"
            bsc_balance_response = requests.get(bsc_balance_url)

            if bsc_balance_response.status_code == 200:
                try:
                    bsc_balance_data = bsc_balance_response.json()
                    for data in bsc_balance_data['result']:
                        address = data['account']
                        balance_wei = int(data['balance'])
                        balance_bnb = balance_wei / 1e18
                        bsc_balances[address] = balance_bnb
                    return
                except Exception as e:
                    print(f"Error processing")

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


while True:
    try:
        main()
    except Exception as e:
        print(f"Error Happend....! Resatarting in 10s")
    time.sleep(10)

    
    
