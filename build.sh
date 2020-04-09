set -e
echo "Starting build"
echo "Starting build"
echo "Starting build"
python setup.py install
echo "Installed packages"
echo "Installed packages"
echo "Installed packages"
python manage.py makemigrations
python manage.py migrate
coverage run --source='smfhcp.views,smfhcp.utils' manage.py test smfhcp.test
coverage html
coverage report
flake8
python manage.py runserver