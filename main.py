from fasthtml.fastapp import *
import sqlite3
import medal_table
import population

app, rt = fast_app(live=False)

@app.on_event("startup")
async def startup_event():
    '''
    Creates database. We create the population table first due to the
    foreign key relationship between medal and population tables
    '''
    try:
        population.create_table()
    except sqlite3.Error as e:
        print(f'ERROR: Failed to create population table: {e}')
        return

    try:
        medal_table.create_table()
    except sqlite3.Error as e:
        print(f'ERROR: Failed to create medals table: {e}')
        return

    print('SUCCESS: Created medal table database')


def create_medal_table():
    conn = sqlite3.connect(medal_table.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.*,
               COALESCE(p1.population, p2.population) AS population
        FROM medals m
        LEFT JOIN population p1 ON m.country_name = p1.entity
        LEFT JOIN population p2 ON m.country_code = p2.code
    ''')
    rows = cursor.fetchall()

    html_rows = []
    for row in rows:
        order = Td(row[0])
        flag_url = row[1]
        country_code = row[2]
        country_name = row[3]
        country = Td(Div(Img(src=flag_url, alt="", width="20px"), Span(f"{country_name} ({country_code})")))
        gold = Td(row[4])
        silver = Td(row[5])
        bronze = Td(row[6])
        total = Td(row[7])
        population = Td(format(row[8], ','))
        pop_per_medal = Td(format(int(row[8] / row[7]), ','))
        html_rows.append(Tr(order, country, gold, silver, bronze, total, population, pop_per_medal))

    conn.close()

    flds = ['Rank', 'Country', 'Gold', 'Silver', 'Bronze', 'Total', 'Population', 'Population per Medal']
    head = Thead(*map(Th, flds))
    return Table(head, *html_rows)

@rt("/")
async def get():
    table = create_medal_table()
    return Titled("2024 Olympics Medal Table", table)

serve()

