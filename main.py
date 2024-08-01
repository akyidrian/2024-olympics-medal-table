from fasthtml.fastapp import *
import sqlite3
import medals_table

app, rt = fast_app(live=True)

@app.on_event("startup")
async def startup_event():
    medals_table.run()

def medal_table():
    conn = sqlite3.connect('olympics_medals.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM medals ORDER BY order_number')
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
        html_rows.append(Tr(order, country, gold, silver, bronze, total))

    conn.close()

    flds = ['Rank', 'Country', 'Gold', 'Silver', 'Bronze', 'Total']
    head = Thead(*map(Th, flds))
    return Table(head, *html_rows)

@rt("/")
async def get():
    table = medal_table()
    return Titled("2024 Olympics Medal Table", table)

serve()

