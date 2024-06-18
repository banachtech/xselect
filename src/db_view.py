import sqlite3

def check_tables(database_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    # Query to get the list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    
    # Fetch all results from the executed query
    tables = cursor.fetchall()
    
    # If there are tables, print their names
    if tables:
        print("Tables in the database:")
        for table in tables:
            print(table[0])
    else:
        print("No tables found in the database.")
    
    # Close the connection
    cursor.close()
    conn.close()

def view_table(database_path, table_name):
    # Connect to the SQLite database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    # Query to get the data from the table
    cursor.execute(f"SELECT * FROM {table_name}")
    
    # Fetch all results from the executed query
    rows = cursor.fetchall()
    
    # Get the column names
    column_names = [description[0] for description in cursor.description]
    
    # Print the column names
    print(f"Table: {table_name}")
    print(", ".join(column_names))
    
    # Print each row
    for row in rows:
        print(row)
    
    print(len(rows))
    print(", ".join(column_names))
    
    # Close the connection
    cursor.close()
    conn.close()

def main():
    database_path = "data/finance_data.db"  # Path to your SQLite database
    tables = ["company_overviews"] #,"historical_prices","quaterly_earnings"] # 
    
    for table in tables[0:]:
        view_table(database_path, table)
        print("\n")
        print(len(tables))

if __name__ == "__main__":
    main()
