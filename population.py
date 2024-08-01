import pandas as pd
import sqlite3


DATABASE_NAME = 'medal_table.db'


def create_table():
    data_frame = pd.read_csv('population.csv')

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

    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS population (
            entity TEXT PRIMARY KEY,
            code TEXT,
            year INTEGER,
            population INTEGER
        )
        ''')
    except sqlite3.Error as e:
        print(f"An error occurred while create the population table: {e}")
        print("FAILED: Data has not been commited to the SQLite database")
        conn.close()
        return


    # Insert the data into the SQLite table
    for row in result.itertuples(index=False):
        try:
            cursor.execute('''
            INSERT OR REPLACE INTO population (entity, code, year, population)
            VALUES (?, ?, ?, ?)
            ''', (row.Entity, row.Code, row.Year, row._3))
        except sqlite3.Error as e:
            print(f"An error occurred: {e}. Failed to insert row: {row}")
            print("FAILED: Data has not been commited to the SQLite database")
            conn.close()
            return

    print("SUCCESS: Data has been commited to the SQLite database")
    conn.commit()
    conn.close()


if __name__ == '__main__':
    create_table()

