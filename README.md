 # Чат Бот для знакомств в Vkontakte
![Python](https://img.shields.io/badge/PYTHON-3.8.6-yellow/?style=for-the-badge&color=9cf&logo=python&labelColor=brown) ![vkapi](https://img.shields.io/badge/Vkontakte-VkAPI-informational/?style=for-the-badge&color=informational&logo=vkontakte) ![Postgres](https://img.shields.io/badge/Database-PostgreSQL-orange/?style=for-the-badge&color=red&logo=postgresql&labelColor=black&link=https://www.postgresql.org)
### Задачи которые выполняет Бот:
1. Ищет людей, подходящих под условия, на основании информации о пользователе из VK:

* Возраст, пол, город.

*  Если информации недостаточно Бот дополнительно уточнит её у пользователя.

2. У тех людей, которые подошли по требованиям пользователю на основании профиля и запрошенных данных, получает топ-3 популярных фотографии профиля и отправляет их пользователю в чат вместе со ссылкой на найденного человека. Популярность определяется по количеству лайков к фото.

3. Добавляет человека в избранный список, используя БД PostgreSQL.

--------
### Для работы Бота в чате в Vkontakte Вам понадобится:
1. Сообщество, от имени которого ваш бот будет общаться с пользователями ВКонтакте. 
2. Токен сообщества 
3. Токен пользователя


### Активация Бота:
1. Заполнить в файле config.py: VK_USERS_TOKEN (токен пользователя), VK_GROUP_TOKEN (токен сообщества), database_name (имя используемой БД), database_user (имя пользователя БД), database_password (пароль от БД)  

2. Установить недостающие библиотеки, указанные в файле requirements.txt

3. Создать таблицы для работы Бота, запустив файл Netology_project_DB.py.

4. Запустить файл Netology_project_bot.py.

5. Активировать Бота словом "Начать" в чате ВКонтакте.