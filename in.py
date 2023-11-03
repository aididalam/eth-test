import time
import os
import sys
import random
import threading
import csv
from eth_account import Account
Account.enable_unaudited_hdwallet_features()

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "english.txt")

csv_file_path = os.path.join(script_dir, "ad.csv")

           
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
        with open(csv_file_path, mode='a', newline='') as csv_file:
            fieldnames = ["private_key", "public_key", "seed_phrase"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            # Write the data to the CSV file
            writer.writerow({"private_key": private_key, "public_key": public_key, "seed_phrase": seed_phrase})

        sys.stdout.write("\rSeed: " + seed_phrase)
        sys.stdout.flush()  # Flush the output to make it visible immediately
    except Exception as e:
        pass      

def main():
    with open(file_path, "r") as file:
        word_list = [word.strip() for word in file]

    # Define the number of words to combine
    num_words_to_combine = 12

    # Define the seed and positions for the first 12 words
    start_words="baby baby baby baby baby baby baby baby baby baby baby baby"
    seed_words = start_words
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
        print("An error occurred: {e}. Restarting in 60 seconds...")
        time.sleep(2)