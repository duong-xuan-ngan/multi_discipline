
import os
import csv
import json


with open('user.csv', 'r') as file:
    csv_reader = csv.reader(file)
    print(csv_reader)
    next(csv_reader)  # Skip header
    for row in csv_reader:
        print(row)
