from fasthtml.fastapp import *
import asyncio
import medal_table
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
    foreign key relationship between medal and population tables
    '''
    remapping = {"Taiwan": ("Chinese Taipei", "TPE")}
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

    # TODO: Not exactly true that we're always creating the table...
    #       Most of the time we're probably just updating the existing tables...
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

        print('SUCCESS: Updated medal table database')


@app.on_event("startup")
async def startup_event():
    create_database()
    asyncio.create_task(background_task())


def create_world_winners_row(query_rows):
    gold = 0
    silver = 0
    bronze = 0
    total = 0
    pop = 0
    for r in query_rows:
        gold += r[4]
        silver += r[5]
        bronze += r[6]
        total += r[7]
        pop += r[8]

    world_winners = Div(Img(src=OLYMPIC_RINGS_URL, alt="", width="20px"), 
                        Span("World Winners"))
    population = format(pop, ',')
    population_per_medal = format(pop//total, ',')
    world_winners_row = map(Td, (0, world_winners, gold, silver, bronze, total, population, population_per_medal))
    return Tr(*world_winners_row)


def create_country_row(query_row):
        order, flag_url, country_code, country_name, gold, silver, bronze, total, pop = query_row
        country = Div(Img(src=flag_url, alt="", width="20px"),
                      Span(f"{country_name} ({country_code})"))
        population = format(pop, ',')
        population_per_medal = format(pop//query_row[7], ',')
        country_row = map(Td, (order, country, gold, silver, bronze, total, population, population_per_medal))
        return Tr(*country_row)


# TODO: Maybe there is a more Fast HTML way instead of using sqlite3?
def create_medal_table():
    conn = sqlite3.connect(medal_table.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.*,
               COALESCE(p1.population, p2.population, 0) AS population
        FROM medals m
        LEFT JOIN population p1 ON m.country_name = p1.entity
        LEFT JOIN population p2 ON m.country_code = p2.code
    ''')
    query_rows = cursor.fetchall()
    conn.close()

    sorted_query_rows = sorted(query_rows, key=lambda r: (r[0], r[3]), reverse=False)
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

