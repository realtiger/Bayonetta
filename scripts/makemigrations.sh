if [ -z "$1" ]; then
    echo "Please provide a comment for the migration"
    exit 1
fi
file_absolute_path=$(readlink -f "$0")
dir_absolute_path=$(dirname "$file_absolute_path")
cd "$dir_absolute_path"/../program || exit 1
echo "Making migrations for $1"
alembic revision --autogenerate -m "$1"
echo "Migrations created"
cd - || exit 1
