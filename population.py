import pandas as pd
import sqlite3


DATABASE_NAME = 'medal_table.db'
CSV_FILE_PATH = 'population.csv' # assuming it's in 'this' directory


def create_table():
    data_frame = pd.read_csv(CSV_FILE_PATH)

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
    conn = sqlite3.connect(DATABASE_NAME)
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
        cursor.execute('''
        INSERT OR REPLACE INTO population (entity, code, year, population)
        VALUES (?, ?, ?, ?)
        ''', (row.Entity, row.Code, row.Year, row._3))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    try:
        create_table()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        print("FAILED: Data has not been commited to the SQLite database")
    print("SUCCESS: Data has been commited to the SQLite database")

