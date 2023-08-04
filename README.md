# Foodrgam

Продуктовый помощник - дипломный проект курса Backend-разработки Яндекс.Практикума. На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

Проект реализован на `Django` и `DjangoRestFramework`. Доступ к данным реализован через API-интерфейс. 


### Технологии:

Python, Django, Django Rest Framework, Docker, Gunicorn, NGINX, PostgreSQL, Yandex Cloud, Continuous Integration, Continuous Deployment

## Локальный запуск проекта

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:KenshinLove/foodgram-project-react.git
cd foodgram-project-react
```

Cоздать и активировать виртуальное окружение, установить зависимости:

```
python3 -m venv venv && \ 
    source venv/scripts/activate && \
    python -m pip install --upgrade pip && \
    pip install -r backend/requirements.txt
```

Установите [docker](https://www.docker.com/) на свой компьютер.

Запустите проект через docker-compose:

```
docker compose -f docker-compose.yml up -d
```

Выполните миграции:

```
docker compose -f docker-compose.yml exec backend python manage.py migrate
```

Соберите статику и скопируйте ее:

```
docker compose -f docker-compose.yml exec backend python manage.py collectstatic  && \
docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

Загрузите игредиенты в базу данных:

```
docker compose -f docker-compose.yml exec backend python manage.py load_ingredients
```

Создайте суперпользователя:

```
docker compose -f docker-compose.yml exec backend python manage.py createsuperuser
```

## .env

В корне проекта создайте файл .env и пропишите в него свои данные.

Пример:

```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=foodgram
```

## Workflow

Для деплоя сайта проекта на удаленный сервер, в репозитории GitHub Actions `Settings/Secrets/Actions` создать Secrets - переменные окружения для доступа к сервисам:

```
DOCKER_USERNAME                # имя пользователя в DockerHub
DOCKER_PASSWORD                # пароль пользователя в DockerHub
HOST                           # ip_address сервера
USER                           # имя пользователя на сервере
SSH_KEY                        # приватный ssh-ключ (cat ~/.ssh/id_rsa)
PASSPHRASE                     # кодовая фраза (пароль) для ssh-ключа
```
На сервере нужно создать папку foodgram, в ней файл .env и папку infra. В папке infra создать файл
nginx.conf. Его содержание должно быть таким же, как у файла infra/nginx.conf в проекте.

Сейчас проект развернут по адресу kenshin.zapto.org
Логин и пароль для доступа в админку

admin@admin.ru 
admin

## Автор
## Александр Карели

