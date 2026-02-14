import mysql.connector
import os
from urllib.parse import unquote

# Hardcoded credentials from .env for debugging
# DATABASE_URL=mysql+mysqlconnector://root:392766yyc%40%21@localhost:3306/beyondu_test?charset=utf8mb4
# Password is URL encoded: 392766yyc%40%21 -> 392766yyc@!

config = {
  'user': 'root',
  'password': unquote('392766yyc%40%21'),
  'host': 'localhost',
  'database': 'beyondu_test',
  'raise_on_warnings': True
}

print(f"Attempting to connect with user='{config['user']}', host='{config['host']}'")

try:
  cnx = mysql.connector.connect(**config)
  print("Connection successful!")
  
  cursor = cnx.cursor()
  
  # Try to drop tables manually here if connection works
  print("Dropping all tables...")
  cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
  
  cursor.execute("SHOW TABLES")
  tables = [table[0] for table in cursor]
  for table in tables:
      print(f"Dropping table {table}...")
      cursor.execute(f"DROP TABLE `{table}`")
      
  cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
  print("All tables dropped.")
  
  cursor.close()
  cnx.close()
  
except mysql.connector.Error as err:
  print(f"Error: {err}")
