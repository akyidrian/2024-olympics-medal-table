from fasthtml.fastapp import *
import asyncio
import medal_table
import population
import sqlite3
import random

OLYMPIC_RINGS_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Olympic_rings_without_rims.svg/200px-Olympic_rings_without_rims.svg.png"

app, rt = fast_app(live=False)

def create_database():
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


async def background_task():
    while True:
        await asyncio.sleep(1800 + int(random.uniform(-600, 600))) # Sleep for somewhere around 20-40mins
        create_database()
        try:
            medal_table.update_table()
        except sqlite3.Error as e:
            print(f'ERROR: Failed to create medals table: {e}')
            return

        print('SUCCESS: Created medal table database')

@app.on_event("startup")
async def startup_event():
    create_database()
    asyncio.create_task(background_task())


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
    conn.close()

    # TODO: Need to make to robust to rank and to allow user interactive sorting
    html_rows = [None] * 1 # Creating a placeholder element for the "World Winners"
    total_gold = 0
    total_silver = 0
    total_bronze = 0
    grand_total = 0
    population_winners = 0
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
        pop_per_medal = Td(format(row[8]//row[7], ','))
        html_rows.append(Tr(order, country, gold, silver, bronze, total, population, pop_per_medal))

        total_gold += row[4]
        total_silver += row[5]
        total_bronze += row[6]
        grand_total += row[7]
        population_winners += row[8]

    world_winners = Td(Div(Img(src=OLYMPIC_RINGS_URL, alt="", width="20px"), Span("World Winners")))
    html_rows[0] = Tr(Td(0), world_winners, Td(total_gold), Td(total_silver), Td(total_bronze), Td(grand_total), Td(format(population_winners, ',')), Td(format(population_winners//grand_total, ',')))

    flds = ['Rank', 'Country', 'Gold', 'Silver', 'Bronze', 'Total', 'Population', 'Pop. per Medal']
    head = Thead(*map(Th, flds))
    return Div(P(Table(head, *html_rows)))

@rt("/")
async def get():
    table = create_medal_table()
    return Titled("2024 Olympics Medal Table", table)

serve()

