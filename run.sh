until pg_isready -h db -p 5432
do
  sleep 2.5
done

echo "Initializing DB"
python create_db.py
echo "Done with DB initialization"

