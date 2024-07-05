import asyncpg
import numpy as np
import asyncio
from datetime import datetime

pg_settings = {
    'user': 'test',
    'password': 'test',
    'database': 'postgres',
    'host': 'localhost',
    'port': '5432',
    'table_name': 'diagram'
}

async def create_table(conn, table_name):
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        timestamp BIGINT NOT NULL,
        x DOUBLE PRECISION NOT NULL,
        y DOUBLE PRECISION NOT NULL
    );
    """
    await conn.execute(create_table_query)

async def insert_data():
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 30)
    total_seconds = int((end_date - start_date).total_seconds())

    timestamps = np.arange(int(start_date.timestamp()), int(end_date.timestamp()), 1)

    conn = await asyncpg.connect(
        user=pg_settings['user'],
        password=pg_settings['password'],
        database=pg_settings['database'],
        host=pg_settings['host'],
        port=pg_settings['port']
    )

    await create_table(conn, pg_settings['table_name'])

    batch_size = 10000
    for start_idx in range(0, total_seconds, batch_size):
        end_idx = min(start_idx + batch_size, total_seconds)
        batch_timestamps = timestamps[start_idx:end_idx]

        num_samples = end_idx - start_idx
        x_base = np.linspace(start_idx, end_idx, num_samples)
        y_base = np.linspace(start_idx, end_idx, num_samples)

        noise_amplitude = batch_size
        x = x_base + np.random.uniform(-noise_amplitude, noise_amplitude, num_samples)
        y = y_base + np.random.uniform(-noise_amplitude, noise_amplitude, num_samples)

        records = [(int(batch_timestamps[i]), float(x[i]), float(y[i])) for i in range(end_idx - start_idx)]
        
        values = ', '.join(f"({record[0]}, {record[1]}, {record[2]})" for record in records)
        insert_query = f"INSERT INTO diagram (timestamp, x, y) VALUES {values}"
        
        await conn.execute(insert_query)

    await conn.close()

    print("Data inserted into PostgreSQL table successfully.")

asyncio.run(insert_data())