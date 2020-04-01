echo "Starting build"
echo "Starting build"
echo "Starting build"
python setup.py install
echo "Installed packages"
echo "Installed packages"
echo "Installed packages"
python manage.py makemigrations
python manage.py migrate
flake8
python manage.py runserver