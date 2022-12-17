This is the code base for an anonymous submission portal. It is to be used in conjunction with an external application, such as Facebook or Instagram.

Dev (Personal) Notes:

set up dev environment:
    "./startup.sh"

Add new group:
    "./scripts/newgroup.py"

Legacy Notes:

enter Django environment:
    "djactivate"
start local server:
    "heroku local"
    "./scripts/runlocal.sh"
view database:
    "heroku pg:psql"
    "./scripts/rundb.sh"
apply change to database:
    "python manage.py makemigrations"
    "python manage.py migrate"
deploy:
    "git push heroku master"
