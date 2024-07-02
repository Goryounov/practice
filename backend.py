from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import asyncpg

pg_settings = {
    'user': 'test',
    'password': 'test',
    'database': 'postgres',
    'host': 'localhost',
    'port': '5432',
    'table_name': 'diagram'
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/diagram/aggregate')
async def diagram_aggregate(from_time, to_time, canvas_width, canvas_height):
    conn = await asyncpg.connect(
        user=pg_settings['user'],
        password=pg_settings['password'],
        database=pg_settings['database'],
        host=pg_settings['host'],
        port=pg_settings['port']
    )

    from_time = int(from_time)
    to_time = int(to_time)
    canvas_width = int(canvas_width)
    canvas_height = int(canvas_height)

    start_execution_time = time.perf_counter()

    min_max_query = f"""
        WITH filtered_data AS (
            SELECT *
            FROM {pg_settings['table_name']}
            WHERE timestamp BETWEEN {from_time} AND {to_time}
        )
        SELECT MAX(x) AS max_x,
            MIN(x) AS min_x,
            MAX(y) AS max_y,
            MIN(y) AS min_y
        FROM filtered_data
    """
    
    bounds = await conn.fetchrow(min_max_query)
    max_x = bounds['max_x']
    min_x = bounds['min_x']
    max_y = bounds['max_y']
    min_y = bounds['min_y']

    sql_query = f"""
        WITH filtered_data AS (
            SELECT *
            FROM {pg_settings['table_name']}
            WHERE timestamp BETWEEN {from_time} AND {to_time}
        ), paddings AS (
            SELECT ROUND({min_x} / (({max_x} - {min_x}) / {canvas_width})) AS padding_x,
                ROUND({min_y} / (({max_y} - {min_y}) / {canvas_height})) AS padding_y
        )
        SELECT DISTINCT ON (
                ROUND(x / (({max_x} - {min_x}) / {canvas_width})) - paddings.padding_x, 
                ROUND(y / (({max_y} - {min_y}) / {canvas_height})) - paddings.padding_y)
            x,
            y,
            ROUND(x / (({max_x} - {min_x}) / {canvas_width})) - paddings.padding_x AS pixel_x,
            ROUND(y / (({max_y} - {min_y}) / {canvas_height})) - paddings.padding_y AS pixel_y
        FROM filtered_data,
            paddings
    """
    
    records = await conn.fetch(sql_query)

    end_execution_time = time.perf_counter()
    elapsed_time = end_execution_time - start_execution_time

    await conn.close()

    return {"records": records, "query_execution_time": elapsed_time, "bounds": bounds}


@app.get('/diagram')
async def diagram(from_time, to_time):
    conn = await asyncpg.connect(
        user=pg_settings['user'],
        password=pg_settings['password'],
        database=pg_settings['database'],
        host=pg_settings['host'],
        port=pg_settings['port']
    )

    from_time = int(from_time)
    to_time = int(to_time)

    start_execution_time = time.perf_counter()

    sql_query = f"""
        SELECT * FROM {pg_settings['table_name']} WHERE timestamp BETWEEN {from_time} AND {to_time}
    """
    records = await conn.fetch(sql_query)

    end_execution_time = time.perf_counter()
    elapsed_time = end_execution_time - start_execution_time

    await conn.close()

    return {"records": records, "query_execution_time": elapsed_time}
