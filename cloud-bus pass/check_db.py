import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
# Get the list of all tables in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables found in database:", tables)

# Print data for each table automatically
for table in tables:
    table_name = table[0]
    print(f"\n--- Data in table '{table_name}' ---")
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

conn.close()