import psycopg2

conn = psycopg2.connect(
    database="knitting",
    user="postgres",
    password="55555",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# # Function to delete existing data in the users table
# def delete_existing_users():
#     try:
#         cur.execute("DELETE FROM users")
#         conn.commit()
#         print("Existing data in the users table deleted successfully.")
#     except psycopg2.Error as e:
#         print(f"Error deleting existing data in the users table: {e}")

# Function to add new user and password
def add_user(username, password):
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        print(f"User '{username}' added successfully.")
    except psycopg2.Error as e:
        print(f"Error adding user '{username}': {e}")

# # Delete existing data in the users table
# delete_existing_users()

# Add new user-password pairs
user_password_pairs = [
    ("vishnu", "123"),
    ("joel", "123"),
    ("countai", "123")
]

for username, password in user_password_pairs:
    add_user(username, password)

# Close database connection
cur.close()
conn.close()
