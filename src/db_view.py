import sqlite3

def check_tables(database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    
    tables = cursor.fetchall()
    
    if tables:
        print("Tables in the database:")
        for table in tables:
            print(table[0])
    else:
        print("No tables found in the database.")
    
    cursor.close()
    conn.close()

def view_table(database_path, table_name):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT * FROM {table_name}")
    
    rows = cursor.fetchall()
    
    column_names = [description[0] for description in cursor.description]
    
    print(f"Table: {table_name}")
    print(", ".join(column_names))
    
    for row in rows:
        print(row)
    
    print(len(rows))
    print(", ".join(column_names))
    
    cursor.close()
    conn.close()

def main():
    database_path = "data/finance_data.db" 
    
    tables = ["company_overviews"] 
    
    for table in tables[0:]:
        view_table(database_path, table)
        print("\n")
        print(len(tables))

if __name__ == "__main__":
    main()

