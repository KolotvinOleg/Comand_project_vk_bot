from datetime import date
from second_bot.config import my_token, group_token
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from second_bot.db import insert_vk_user, insert_favourite_user, insert_photo
from second_bot.db import session, Favourite_user, Vk_User, Photo


vk_session_bot = vk_api.VkApi(token=group_token)
vk_session_user = vk_api.VkApi(token=my_token)
longpoll = VkLongPoll(vk_session_bot)

def get_user_data(user_id) -> dict:

    result_dict = vk_session_bot.method("users.get",
                                        {"user_ids": user_id, "fields": "city, bdate, sex"})[0]

    def get_age(bday):
        today = date.today()
        years_delta = today.year - bday.year
        new_day = date(bday.year + years_delta, bday.month, bday.day)
        if new_day > today:
            return years_delta - 1
        return years_delta

    result = {"vk_id": user_id, "first_name": result_dict["first_name"], "last_name": result_dict["last_name"]}

    if result_dict["city"]:
        result["city_id"] = result_dict["city"]["id"]
        result["city_title"] = result_dict["city"]["title"]

    if result_dict['bdate']:
        if len(result_dict['bdate']) > 5:
            bdate = result_dict['bdate'].split('.')
            bdate = date(int(bdate[2]), int(bdate[1]), int(bdate[0]))
            age = get_age(bdate)
            result["age"] = age

    if result_dict["sex"] != "0":
        gender = result_dict["sex"]
        if gender == 1:
            result["gender"] = 'female'
        elif gender == 2:
            result["gender"] = 'male'


    return result

def search_users(user_id, offset=None):

    user_data = get_user_data(user_id)


    params = {"sort": "0", "count": "100", "status": (1, 6), "city": user_data["city_id"],
              "age_from": user_data["age"] - 5, "age_to": user_data["age"] + 5, "has_photo": "1", "fields": "is_friend",
              "sex": (1 if user_data["gender"] == "male" else 2)}

    if offset:
        params['offset'] = offset

    result = vk_session_user.method("users.search", params)

    for user in result["items"]:
        if user['is_closed'] is True or user["is_friend"] == 1:
            continue
        yield user

def get_photos(user_id):

    result = vk_session_user.method("photos.get",
                                    {"owner_id": user_id,
                                            "album_id": "profile",
                                            "extended": 1}
                                    )

    result = sorted(result["items"], key=lambda a: a["likes"]["count"], reverse=True)[:3]
    media_ids = []
    for photo in result:
        media_ids.append(photo["id"])
    return tuple(media_ids)

def send_message(user_id, text, keyboard=None, attachment=None):
    params = {'user_id': user_id,
     "message": text,
     'random_id': 0}
    if attachment is not None:
        params["attachment"] = attachment
    if keyboard is not None:
        params["keyboard"] = keyboard.get_keyboard()

    vk_session_bot.method("messages.send", params)


def test_bot():
    offset = 0
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            msg = event.text.lower()

            if msg == 'начать':
                keyboard = VkKeyboard(one_time=True)
                keyboard.add_button(label='Start', color=VkKeyboardColor.PRIMARY)
                send_message(user_id, 'Данный бот подбирает людей для знакомства, нажмите Start', keyboard)

            if msg == 'start':

                id_list = []
                for id in session.query(Vk_User.vk_id).all():
                    id_list.append(id[0])
                if int(user_id) not in id_list:
                    user_data = get_user_data(user_id)
                    insert_vk_user(session, user_data)

                users = search_users(user_id)
                user = next(users)
                if session.query(Favourite_user.vk_id).all():
                    tpl_id = [user["id"]]
                    while (tuple(tpl_id)) in session.query(Favourite_user.vk_id).all():
                        user = next(users, 1)
                        if user == 1:
                            offset += 50
                            users = search_users(user_id, offset=offset)
                            user = next(users)
                        tpl_id = [user["id"]]

                user_data = get_user_data(user_id)
                keyboard_2 = VkKeyboard()
                keyboard_2.add_button(label='Добавить в список избранных', color=VkKeyboardColor.NEGATIVE)
                keyboard_2.add_button(label='Перейти к следующему', color=VkKeyboardColor.POSITIVE)
                keyboard_2.add_line()
                keyboard_2.add_button(label='Посмотреть список избранных', color=VkKeyboardColor.POSITIVE)

                media_ids = get_photos(user["id"])
                attachment = [f'photo{user["id"]}_{media_id}' for media_id in media_ids]
                send_message(user_id,
                             f"Добавить в список избранных?\n{user['first_name']} {user['last_name']}(https://vk.com/id{user['id']})",
                             keyboard_2, attachment=','.join(attachment))
                # send_message_photos(user_id, user["first_name"], user["last_name"], user["id"], media_ids)

            if msg == 'добавить в список избранных':
                user_data = get_user_data(user['id'])
                query = session.query(Vk_User.id).filter(Vk_User.vk_id == user_id).scalar()
                user_data["id_vk_user"] = query
                insert_favourite_user(session, user_data)
                query = session.query(Favourite_user.id).filter(Favourite_user.vk_id == user["id"]).scalar()
                for media_id in media_ids:
                    insert_photo(session, media_id, query)
                send_message(user_id, f"{user['first_name']} {user['last_name']} добавлен в список избранных")

            if msg == 'перейти к следующему':
                user = next(users, 1)
                if user == 1:
                    offset += 50
                    users = search_users(user_id, offset=offset)
                    user = next(users)
                media_ids = get_photos(user["id"])
                attachment = [f'photo{user["id"]}_{media_id}' for media_id in media_ids]
                send_message(user_id,
                             f"Добавить в список избранных?\n{user['first_name']} {user['last_name']}(https://vk.com/id{user['id']})",
                             attachment=','.join(attachment))

            if msg == 'посмотреть список избранных':
                send_message(user_id, "Список избранных:")
                for query in session.query(Favourite_user.first_name + ' ' + Favourite_user.last_name,
                                           Favourite_user.vk_id) \
                        .join(Vk_User) \
                        .filter(Vk_User.vk_id == user_id).all():
                    full_name = query[0]
                    vk_id = query[1]
                    attachment = []
                    print(query)
                    for q in session.query(Photo.media_id).join(Favourite_user).filter(Favourite_user.vk_id == vk_id).all():
                        attachment.append(f"photo{vk_id}_{q[0]}")
                        print(attachment)
                    send_message(user_id, f"{full_name}(https://vk.com/id{vk_id})", attachment=','.join(attachment))


if __name__ == "__main__":
    test_bot()





