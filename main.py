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


def create_world_winners_row(rows):
    gold = 0
    silver = 0
    bronze = 0
    total = 0
    pop = 0
    for row in rows:
        gold += row[4]
        silver += row[5]
        bronze += row[6]
        total += row[7]
        pop += row[8] if row[8] is not None else 0

    world_winners = Div(Img(src=OLYMPIC_RINGS_URL, alt="", width="20px"), 
                        Span("World Winners"))
    population = format(pop, ',')
    population_per_medal = format(pop//total, ',')
    html_rows = map(Td, (0, world_winners, gold, silver, bronze, total, population, population_per_medal))
    return Tr(*html_rows)


def create_country_row(row):
        order, flag_url, country_code, country_name, gold, silver, bronze, total, pop = row
        country = Div(Img(src=flag_url, alt="", width="20px"),
                      Span(f"{country_name} ({country_code})"))
        pop = pop if pop is not None else 0
        population = format(pop, ',')
        population_per_medal = format(pop//row[7], ',')
        html_rows = map(Td, (order, country, gold, silver, bronze, total, population, population_per_medal))
        return Tr(*html_rows)


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
    database_rows = cursor.fetchall()
    conn.close()

    sorted_rows = sorted(database_rows, key=lambda r: (r[0], r[3]), reverse=False)
    html_rows = [create_world_winners_row(sorted_rows)] # World Winners will always be number 1
    for r in sorted_rows:
        html_rows.append(create_country_row(r))

    flds = ['Rank', 'Country', 'Gold', 'Silver', 'Bronze', 'Total', 'Population', 'Population per Medal']
    head = Thead(*map(Th, flds))
    return Table(head, *html_rows)


@rt("/")
async def get():
    table = create_medal_table()
    return Titled("2024 Olympics Medal Table", table)


serve()

