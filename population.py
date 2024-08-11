import pandas as pd
import sqlite3


DATABASE_FILE_PATH = 'medals.db'
_CSV_FILE_PATH = 'population.csv' # assuming it's in 'this' directory


def create_table(remapping = {}):
    data_frame = pd.read_csv(_CSV_FILE_PATH)

    # Group by 'Entity' (country name) and get the index of the row with the maximum year for each group
    latest_indices = data_frame.groupby('Entity')['Year'].idxmax()

    # Use these indices to select the rows with the latest data for each country
    latest_population = data_frame.loc[latest_indices]

    # Sort countries by population in descending order
    latest_population = latest_population.sort_values('Population (historical)', ascending=False)

    # Reset the index in the data frame
    # Not strictly necessary, but good practice to avoid issues down the line...
    latest_population = latest_population.reset_index(drop=True)

    # Select only the relevant columns
    result = latest_population[['Entity', 'Code', 'Year', 'Population (historical)']]

    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS population (
        entity TEXT PRIMARY KEY,
        code TEXT,
        year INTEGER,
        population INTEGER
    )
    ''')

    for row in result.itertuples(index=False):
        entity = row.Entity
        code = row.Code

        # If there is a key match in our remapping dictionary, we want
        # to use a different entity and code to represent that entity
        if row.Entity in remapping:
            entity, code = remapping[row.Entity]

        cursor.execute('''
        INSERT OR REPLACE INTO population (entity, code, year, population)
        VALUES (?, ?, ?, ?)
        ''', (entity, code, row.Year, row._3))

    conn.commit()
    conn.close()


def print_all_rows():
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM population
    ''')
    rows = cursor.fetchall()
    
    for row in rows:
        print(row)

    conn.close()


if __name__ == '__main__':
    try:
        create_table()
    except sqlite3.Error as e:
        print(f'ERROR: Failed to create population table: {e}')
        exit(1)
    print_all_rows()

