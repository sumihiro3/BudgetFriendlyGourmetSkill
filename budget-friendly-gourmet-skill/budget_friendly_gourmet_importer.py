# -*- coding: utf-8 -*-

import csv
import json

import boto3

with open('budget_friendly_gourmet.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('BudgetFriendlyGourmet')
        table.put_item(
            Item={
                "prefecture": row[0],
                "name": row[1],
                "yomi": row[2],
                "detail": row[3]
            }
        )

    
