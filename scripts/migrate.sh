file_absolute_path=$(readlink -f "$0")
dir_absolute_path=$(dirname "$file_absolute_path")
cd "$dir_absolute_path"/../program || exit 1
echo "Migrating database"
alembic upgrade head
echo "Database migrated"
cd - || exit 1
