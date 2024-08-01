import pandas as pd
import sqlite3

# Read the CSV file
df = pd.read_csv('population.csv')

# Function to identify country entries
def is_country(entity):
    non_country_keywords = ['World', 'Africa', 'Asia', 'Europe', 'America', 'Oceania', 'Antarctica',
                            'income', 'region', 'UN', 'excl.', 'countries', 'Country']
    return not any(keyword in entity for keyword in non_country_keywords)

# Filter out non-country entries
df_filtered = df[df['Entity'].apply(is_country)]

# Group by 'Entity' (country) and get the index of the row with the maximum year for each group
latest_indices = df_filtered.groupby('Entity')['Year'].idxmax()

# Use these indices to select the rows with the latest data for each country
latest_population = df_filtered.loc[latest_indices]

# Sort countries by population in descending order
latest_population = latest_population.sort_values('Population (historical)', ascending=False)

# Reset the index
latest_population = latest_population.reset_index(drop=True)

# Select only the relevant columns
result = latest_population[['Entity', 'Code', 'Year', 'Population (historical)']]

# Display the results
print(result)

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('population_data.db')
cursor = conn.cursor()

# Create a new table
cursor.execute('''
CREATE TABLE IF NOT EXISTS population (
    entity TEXT,
    code TEXT,
    year INTEGER,
    population INTEGER
)
''')

# Insert the data into the SQLite table
for row in result.itertuples(index=False):
    cursor.execute('''
    INSERT INTO population (entity, code, year, population)
    VALUES (?, ?, ?, ?)
    ''', (row.Entity, row.Code, row.Year, row._3))

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Data has been successfully added to the SQLite database.")

