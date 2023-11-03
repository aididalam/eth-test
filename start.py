from bitcoinlib.keys import Key
import threading
import sys

factor = 101
div = int("FFFFFF",16)
start_value =   int("000000000000000000000000000000000000000000000003FFFFFFFFED150000", 16) - (div * factor) 
end_value =     int("000000000000000000000000000000000000000000000003FFFFFFFFED150000", 16) - (div * (factor-1))

middle_value = (start_value + end_value) // 2

left_value = start_value
right_value = end_value

def address(private_key, position):
    key = Key(private_key)
    address = key.address()
    if address=="19ZewH8Kk1PDbSNdJ97FP4EiCjTRaZMZQA":
        print("Bitcoin Address:", address,private_key)
    if position == "left" and int(private_key, 16) % 1000 == 0:
        sys.stdout.write("\r")  # Move cursor to the beginning of the line
        sys.stdout.write("Value: " + str(middle_value - int(private_key, 16)) + "   i: "+str(int(private_key, 16)))
        sys.stdout.flush()  # Flush the output
    

while left_value < middle_value or right_value > middle_value:
    for _ in range(1000):
        threading.Thread(target=address, args=(format(left_value, '064x'),"left")).start()
        left_value += 1
        threading.Thread(target=address, args=(format(right_value, '064x'),"right")).start()
        right_value -= 1