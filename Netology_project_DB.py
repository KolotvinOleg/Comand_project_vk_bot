import psycopg2

def create_table(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users_bot(
    user_bot_id INTEGER PRIMARY KEY,
    first_name VARCHAR(40) NOT NULL,
    last_name VARCHAR(40) NOT NULL,
    age INTEGER NOT NULL,
    city_id INTEGER,
    city_title VARCHAR(30),
    gender VARCHAR(10)
    );
    """)
    print('Таблица users_bot успешно создана!')
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vk_users(
    vk_user_id INTEGER PRIMARY KEY,
    first_name VARCHAR(40) NOT NULL,
    last_name VARCHAR(40) NOT NULL,
    age INTEGER NOT NULL,
    city_id INTEGER,
    city_title VARCHAR(30),
    gender VARCHAR(10)
    )
    """)
    print('Таблица vk_users успешно создана!')
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search(
    search_id SERIAL PRIMARY KEY,
    search_date VARCHAR(10),    
    user_bot_id INTEGER NOT NULL REFERENCES users_bot(user_bot_id)
    );
    """)
    print('Таблица search успешно создана!')
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_vk_users(
    search_vk_user_id SERIAL PRIMARY KEY,
    search_id INTEGER NOT NULL REFERENCES search(search_id),
    vk_user_id INTEGER NOT NULL REFERENCES vk_users(vk_user_id),
    favorite BOOL
    );
    """)
    print('Таблица search_vk_users успешно создана!')
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS photos(
    photos_id SERIAL PRIMARY KEY,
    vk_user_id INTEGER NOT NULL REFERENCES vk_users(vk_user_id),
    likes INTEGER,
    photos_link TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    id INTEGER NOT NULL
    );
    """)
    print('Таблица photos успешно создана!')

def add_user_bot(cursor, vk_id, first_name, last_name, age, city_id, city_title, gender):
    cursor.execute("""
    SELECT user_bot_id from users_bot
    """)
    data_bot_users = cursor.fetchall()
    if vk_id not in [int(x[0]) for x in data_bot_users]:
        cursor.execute("""
        INSERT INTO users_bot(user_bot_id, first_name, last_name, age, city_id, city_title, gender)
        VALUES(%s, %s, %s, %s, %s, %s, %s);
        """, (vk_id, first_name, last_name, age, city_id, city_title, gender))

def select_all_vk_users(cursor, user_bot_id=None):
    if user_bot_id is None:
        cursor.execute("""
        SELECT vk_user_id FROM vk_users
        """)
    else:
        cursor.execute("""
        SELECT vk_user_id FROM vk_users
        JOIN search_vk_users USING(vk_user_id)
        JOIN search USING(search_id)
        WHERE user_bot_id = %s
        """, (user_bot_id, ))
    data_vk_users = cursor.fetchall()
    return [x[0] for x in data_vk_users]

def insert_data_in_vk_users(cursor, vk_id, first_name, last_name, age, city_id, city_title, gender):
        cursor.execute("""
        INSERT INTO vk_users(vk_user_id, first_name, last_name, age, city_id, city_title, gender)
        VALUES(%s, %s, %s, %s, %s, %s, %s);
        """, (vk_id, first_name, last_name, age, city_id, city_title, gender))

def insert_data_in_search(cursor, search_date, user_bot_id):
    cursor.execute("""
    INSERT INTO search(search_date, user_bot_id)
    VALUES(%s, %s) RETURNING search_id;
    """, (search_date, user_bot_id))
    search_id = cursor.fetchone()[0]
    return search_id

def insert_data_in_search_vk_users(cursor, search_id, vk_user_id, favorite=False):
    cursor.execute("""
    INSERT INTO search_vk_users(search_id, vk_user_id, favorite)
    VALUES(%s, %s, %s)
    """, (search_id, vk_user_id, favorite))

def insert_data_in_photos(cursor, photos_data):
    for photo in photos_data:
        cursor.execute("""
        INSERT INTO photos(vk_user_id, likes, photos_link, owner_id, id)
        VALUES(%s, %s, %s, %s, %s)
        """, (photo['vk_id'], photo['likes'], photo['photos_link'], photo['owner_id'], photo['id']))

def select_data_from_photos(cursor, vk_id):
    cursor.execute("""
    SELECT owner_id, id FROM photos
    WHERE vk_user_id = %s
    """, (vk_id,))
    result = cursor.fetchall()
    return result

def select_data_from_vk_users(cursor, vk_id):
    cursor.execute("""
    SELECT first_name, last_name FROM vk_users
    WHERE vk_user_id = %s
    """, (vk_id, ))
    result = cursor.fetchone()
    return result

def update_favorite(cursor, vk_id, search_id):
    cursor.execute("""
    UPDATE search_vk_users
    SET favorite = TRUE
    WHERE vk_user_id = %s and search_id = %s
    """, (vk_id, search_id))

def select_favorite_users(cursor, user_bot_id):
    cursor.execute("""
    SELECT vk_user_id, first_name, last_name
    FROM vk_users
    JOIN search_vk_users USING(vk_user_id)
    JOIN search USING(search_id)
    WHERE user_bot_id = %s AND favorite = TRUE
    """, (user_bot_id, ))
    result = cursor.fetchall()
    return result

if __name__ == '__main__':
    with psycopg2.connect(database='netology_project_db', user='postgres', password='123098123Kol') as con:
        with con.cursor() as cur:
            cur.execute("""
            DROP TABLE search_vk_users;
            DROP TABLE search;
            DROP TABLE users_bot;
            DROP TABLE photos;
            DROP TABLE vk_users;
            """)
            create_table(cur)