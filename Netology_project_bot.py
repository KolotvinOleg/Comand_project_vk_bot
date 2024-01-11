import vk_api
import psycopg2
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from datetime import date
from config import VK_GROUP_TOKEN, VK_USERS_TOKEN, database_name, database_user, database_password
from Netology_project_DB import (add_user_bot, select_all_vk_users, insert_data_in_vk_users, insert_data_in_search,
                                 insert_data_in_photos, select_data_from_photos, select_data_from_vk_users,
                                 insert_data_in_search_vk_users, update_favorite, select_favorite_users)


def send_message(user_id, message, attachment=None, keyboard=None):
    '''Функция отправки сообщения в чат бота'''
    post = {'user_id': user_id,
            'message': message,
            'random_id': get_random_id()}
    if attachment is not None:
        post['attachment'] = ','.join(attachment)
    if keyboard is not None:
        post['keyboard'] = keyboard.get_keyboard()
    session.method('messages.send', post)


def get_age(bday: date):
    '''Функция преобразования даты рождения в возраст'''
    today = date.today()
    years_delta = today.year - bday.year
    new_day = date(bday.year + years_delta, bday.month, bday.day)
    if new_day > today:
        return years_delta - 1
    return years_delta


def get_data_to_insert(data):
    '''Функция подготовки данных для добавления в БД'''
    vk_id = data['id']
    first_name = data['first_name']
    last_name = data['last_name']
    if 'city' in data:
        city_title = data['city']['title']
        city_id = data['city']['id']
    else:
        city_title = 'unknown'
        city_id = 0
    bdate = data['bdate']
    if isinstance(bdate, int):
        age = bdate
    else:
        bdate = data['bdate'].split('.')
        bdate = date(int(bdate[2]), int(bdate[1]), int(bdate[0]))
        age = get_age(bdate)
    gender = data['sex']
    if gender == 2:
        gender = 'male'
    elif gender == 1:
        gender = 'female'
    else:
        gender = 'unknown'
    return [vk_id, first_name, last_name, age, city_id, city_title, gender]


def search_users_vk(session, data: list, offset=0):
    """Функция поиска пользователей вк на основании данных о пользователе бота"""
    if data[6] == 'male':
        find_gender = 1
    elif data[6] == 'female':
        find_gender = 2
    params = {
        'hometown': data[5],
        'sex': find_gender,
        'status': (1, 6),
        'age_from': data[3] - 3,
        'age_to': data[3] + 2,
        'has_photo': 1,
        'count': 50,
        'fields': 'bdate,city,sex'
    }
    if offset:
        params['offset'] = offset
    data = session.method('users.search', params)
    return data


def get_data_photos(session, vk_id):
    '''Функция получения данных о 3 самых популярных фотографиях найденного пользователя VK'''
    params = {
        'owner_id': vk_id,
        'album_id': 'profile',
        'extended': 1
    }
    response = session.method('photos.get', params)
    if response['count'] > 3:
        photos = sorted(response['items'], key=lambda x: x['likes']['count'], reverse=True)[0:3]
    else:
        photos = response['items']
    result = []
    for photo in photos:
        result.append({'vk_id': vk_id,
                       'likes': photo['likes']['count'],
                       'photos_link': photo['sizes'][-1]['url'],
                       'owner_id': photo['owner_id'],
                       'id': photo['id']})
    return result


def get_attaachment(cursor, id):
    '''Функция получения аттрибута attachment для отправления фотографий найденного пользователя в чат бота'''
    attachment_data = select_data_from_photos(cursor, id)
    attachment = []
    for photo in attachment_data:
        attachment.append(f'photo{photo[0]}_{photo[1]}')
    return attachment


def check_city(text: str):
    '''Функция проверки наличия в профиле пользователя бота информации о родном городе'''
    if text in ['Начать', 'START', 'NEXT', 'Добавить в список избранных', 'Показать список избранных']:
        return False
    if text.isdigit():
        return False
    if not text.replace(' ', '').isalpha():
        return False
    if not text.replace('-', '').isalpha():
        return False
    return True


keyboard = VkKeyboard(one_time=True)
keyboard.add_button('START', color=VkKeyboardColor.PRIMARY)
keyboard2 = VkKeyboard(one_time=True)
keyboard2.add_button('NEXT', color=VkKeyboardColor.POSITIVE)
keyboard2.add_button('Добавить в список избранных', color=VkKeyboardColor.NEGATIVE)
keyboard2.add_line()
keyboard2.add_button('Показать список избранных', color=VkKeyboardColor.PRIMARY)
session = vk_api.VkApi(token=VK_GROUP_TOKEN)
session2 = vk_api.VkApi(token=VK_USERS_TOKEN)
offset = 0
user_bot_data = {}
with psycopg2.connect(database=database_name, user=database_user, password=database_password) as con:
    with con.cursor() as cur:
        for event in VkLongPoll(session).listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                reseived_message = event.text
                user_bot_id = event.user_id
                if not user_bot_data:
                    data = session.method('users.get',
                                          {'user_ids': user_bot_id,
                                           'fields': 'bdate,city,sex'})
                    user_bot_data = data[0]
                if reseived_message == 'Начать':
                    text_info = ('Данный бот используя данные о Вашем возрасте, поле и городе осуществляет '
                                 'поиск других пользователей вк для знакомств. Для начала поиска нажмите на кнопку START')
                    send_message(user_bot_id, text_info)
                    if 'bdate' not in user_bot_data or len(user_bot_data['bdate'].split('.')) < 3:
                        text = 'На вашей странице вк отсутствуют данные о Вашем возрасте.\
                        Пожалуйста, укажите свой возраст'
                        send_message(user_bot_id, text)
                    elif 'city' not in user_bot_data:
                        text = ('На вашей странице вк отсутствуют данные о Вашм городе. Пожалуйста, укажите '
                                'город для поиска.')
                        send_message(user_bot_id, text)
                    else:
                        send_message(user_bot_id, 'Для начала нажмите кнопку START', keyboard=keyboard)
                if reseived_message.isdigit() and len(reseived_message) == 2:
                    user_bot_data['bdate'] = int(reseived_message)
                    if 'city' in user_bot_data:
                        send_message(user_bot_id, 'Для начала нажмите кнопку START', keyboard=keyboard)
                    else:
                        text = ('На вашей странице вк отсутствуют данные о Вашм городе. Пожалуйста, укажите '
                                'город для поиска.')
                        send_message(user_bot_id, text)
                if check_city(reseived_message):
                    if 'city' not in user_bot_data:
                        user_bot_data['city'] = {'title': reseived_message, 'id': 0}
                        send_message(user_bot_id, 'Для начала нажмите кнопку START', keyboard=keyboard)
                if reseived_message == 'START':
                    data_to_insert = get_data_to_insert(user_bot_data)  # Получение данных о пользователе бота
                    text = 'Идет поиск пользователей ВК, пожалуйста, подождите 1 минуту!'
                    send_message(user_bot_id, text)
                    # Добавляем пользователя бота в таблицу users_bot
                    add_user_bot(cur, *data_to_insert)
                    # Добавляем данные в таблицу search и получаем search_id для добавления в search_vk_users
                    search_id = insert_data_in_search(cur, date.today().strftime('%d.%m.%Y'), user_bot_id)
                    # Находим пользователей вк противоположного пола на основании данных пользователя
                    users_vk = search_users_vk(session2, data_to_insert)
                    # Выбираем id всех сохраненных пользователей вк для исключения повторения в таблице vk_users
                    data_vk_users = select_all_vk_users(cur)
                    for user in users_vk['items']:
                        data_to_insert_in_table = get_data_to_insert(user)
                        if data_to_insert_in_table[0] not in data_vk_users:
                            # Добавляем найденных пользователей vk в таблицу vk_users
                            insert_data_in_vk_users(cur, *data_to_insert_in_table)
                            photos_data = get_data_photos(session2, data_to_insert_in_table[0])
                            # Добавляем данные о фотографиях найденных пользователей в таблицу photos
                            insert_data_in_photos(cur, photos_data)
                        # Добавляем данные в таблицу search_vk_users
                        insert_data_in_search_vk_users(cur, search_id, data_to_insert_in_table[0])
                    # Находим id всех найденных пользователей vk, которых будем последовательно отправлять в
                    # сообщениях при нажатии кнопки NEXT
                    data_vk_users = select_all_vk_users(cur, user_bot_id, search_id)
                    # Создаем итератор для последовательной отправки сообщений с информацией о пользователях
                    # Данные о первом пользователе передаются при нажатии кнопки START, далее по одному при нажатии
                    # кнопки NEXT
                    my_iter = iter(data_vk_users)
                    next_people = next(my_iter)
                    first_and_lastname = select_data_from_vk_users(cur, next_people)
                    attachment = get_attaachment(cur, next_people)
                    send_message(user_bot_id, f'{first_and_lastname[0]} {first_and_lastname[1]}\n'
                                              f'vk.com/id{next_people}', attachment=attachment, keyboard=keyboard2)
                if reseived_message == 'NEXT':
                    try:
                        next_people = next(my_iter)
                    except StopIteration:
                        offset += 50
                        send_message(user_bot_id, text)
                        # Добавляем данные в таблицу search и получаем search_id для добавления в search_vk_users
                        search_id = insert_data_in_search(cur, date.today().strftime('%d.%m.%Y'), user_bot_id)
                        # Находим следующих 50 пользователей вк противоположного пола на основании
                        # данных пользователя бота
                        users_vk = search_users_vk(session2, data_to_insert, offset)
                        # Выбираем id всех сохраненных пользователей вк для исключения повторения
                        data_vk_users = select_all_vk_users(cur)
                        for user in users_vk['items']:
                            data_to_insert_in_table = get_data_to_insert(user)
                            if data_to_insert_in_table[0] not in data_vk_users:
                                # Добавляем найденных пользователей vk в таблицу vk_users
                                insert_data_in_vk_users(cur, *data_to_insert_in_table)
                                photos_data = get_data_photos(session2, data_to_insert_in_table[0])
                                # Добавляем данные о фотографиях найденных пользователей в таблицу photos
                                insert_data_in_photos(cur, photos_data)
                                # Добавляем данные в таблицу search_vk_users
                            insert_data_in_search_vk_users(cur, search_id, data_to_insert_in_table[0])
                        # Находим id всех следующих 50 найденных пользователей vk, которых будем последовательно
                        # отправлять в сообщениях при нажатии кнопки NEXT
                        data_vk_users = select_all_vk_users(cur, user_bot_id, search_id)
                        my_iter = iter(data_vk_users)
                        next_people = next(my_iter)
                    first_and_lastname = select_data_from_vk_users(cur, next_people)
                    attachment = get_attaachment(cur, next_people)
                    send_message(user_bot_id, f'{first_and_lastname[0]} {first_and_lastname[1]}\n'
                                              f'vk.com/id{next_people}', attachment, keyboard=keyboard2)
                if reseived_message == 'Добавить в список избранных':
                    update_favorite(cur, next_people, search_id)
                    send_message(user_bot_id, f'{first_and_lastname[0]} {first_and_lastname[1]} '
                                              f'добавлен(а) в список избранных', keyboard=keyboard2)
                if reseived_message == 'Показать список избранных':
                    favorite_users_data = select_favorite_users(cur, user_bot_id)
                    if not favorite_users_data:
                        send_message(user_bot_id, 'Список избранных людей пуст.')
                    send_message(user_bot_id, 'СПИСОК ИЗБРАННЫХ:', keyboard=keyboard2)
                    for favorite_user_data in favorite_users_data:
                        attachment = get_attaachment(cur, favorite_user_data[0])
                        send_message(user_bot_id, f'{favorite_user_data[1]} {favorite_user_data[2]}\n'
                                                  f'vk.com/id{favorite_user_data[0]}', attachment)