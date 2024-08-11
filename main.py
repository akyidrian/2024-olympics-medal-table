from fasthtml.fastapp import *
import asyncio
import fastlite
import medal_table
import os
import population
import sqlite3
import random

OLYMPIC_RINGS_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Olympic_rings_without_rims.svg/200px-Olympic_rings_without_rims.svg.png"

main_stylesheet = Link(rel="stylesheet", href="main.css")
main_script = Script(src="main.js")
app, rt = fast_app(live=False, hdrs=(main_stylesheet, main_script))

def create_database():
    '''
    Creates database. We create the population table first due to the
    foreign key relationship between medal and population tables.
    '''
    remapping = {
        "Taiwan": ("Chinese Taipei", "TPE"),
        "Iran": ("Islamic Republic of Iran", "IRI")
    }
    try:
        population.create_table(remapping)
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
        try:
            medal_table.update_table()
        except sqlite3.Error as e:
            print(f'ERROR: Failed to create medals table: {e}')
            return

        print('SUCCESS: Updated medal table database')


@app.on_event("startup")
async def startup_event():
    # If the database file doesn't already exist, we'll
    # attempt to create and continually update the database.
    # Since the 2024 Olympics are now complete, there is no
    # guarentee creating and updating the database will
    # work correctly...
    if not os.path.isfile(medal_table.DATABASE_FILE_PATH):
        print("INFO: Database does not already exist")
        create_database()
        asyncio.create_task(background_task())
    else:
        print("INFO: Database already exists")


def create_world_winners_row(query_rows):
    gold = 0
    silver = 0
    bronze = 0
    total = 0
    pop = 0
    for r in query_rows:
        gold += r['gold']
        silver += r['silver']
        bronze += r['bronze']
        total += r['total_medals']
        pop += r['population']

    world_winners = Div(Img(src=OLYMPIC_RINGS_URL, alt="", width="20px"), 
                        Span("World Winners"))
    population = format(pop, ',')
    population_per_medal = format(pop//total, ',') if total > 0 else '0'
    world_winners_row = map(Td, (0, world_winners, gold, silver, bronze, total, population, population_per_medal))
    return Tr(*world_winners_row)


def create_country_row(query_row):
        order = query_row['order_number']
        flag_url = query_row['flag_url']
        country_name = query_row['country_name']
        country_code = query_row['country_code']
        gold = query_row['gold']
        silver = query_row['silver']
        bronze = query_row['bronze']
        total = query_row['total_medals']
        pop = query_row['population']
        country = Div(Img(src=flag_url, alt="", width="20px"),
                      Span(f"{country_name} ({country_code})"))
        population = format(pop, ',')
        population_per_medal = format(pop//total, ',')
        country_row = map(Td, (order, country, gold, silver, bronze, total, population, population_per_medal))
        return Tr(*country_row)


def create_medal_table():
    db = fastlite.database(medal_table.DATABASE_FILE_PATH)
    query = '''
        SELECT m.*,
               COALESCE(p1.population, p2.population, 0) AS population
        FROM medals m
        LEFT JOIN population p1 ON m.country_name = p1.entity
        LEFT JOIN population p2 ON m.country_code = p2.code
    '''
    query_rows = db.q(query)

    sorted_query_rows = sorted(query_rows, key=lambda r: (r['order_number'], r['country_name']), reverse=False)
    table_rows = [create_world_winners_row(sorted_query_rows)] # World Winners will always be number 1 (rank 0)
    for r in sorted_query_rows:
        table_rows.append(create_country_row(r))

    flds = ['Rank', 'Country', 'Gold', 'Silver', 'Bronze', 'Total', 'Population', 'Population per Medal']
    head = Thead(*map(Th, flds))
    return Table(head, *table_rows)


@rt("/")
async def get():
    table = create_medal_table()
    return Titled("2024 Olympics Medal Table", table)


serve()

