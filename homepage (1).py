import streamlit as st
import json
from datetime import datetime
import psycopg2
import os
import hashlib

######################################################################LOGIN PAGE ##################################################################################

# Database connection
conn = psycopg2.connect(
    database="Annotation_department",
    user="postgres",
    password="vishnu123",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Constants
LOG_FILE = "login_logs.json"
PARSED_FILE = "parsed_data.json"


# Function to create login logs table if not exists
def create_login_logs_table(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS login_logs (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50),
                timestamp TIMESTAMP
            );
        """)
        conn.commit()

    except psycopg2.Error as e:
        st.error(f"Error creating login logs table: {e}")

# Function to check if a user exists
def user_exists(username):
    cur.execute("SELECT username FROM users WHERE username = %s", (username,))
    return cur.fetchone() is not None


# Login Function
def login(username, password):
    # Retrieve the hashed password from the database based on the username
    cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    hashed_password = cur.fetchone()
    
    if hashed_password:
        # Check if the provided password matches the hashed password
        if hash_password(password) == hashed_password[0]:
            return True
    return False


# Registration Function
def register(username, password):
    # Check if the user already exists
    if user_exists(username):
        st.error("User already exists. Please choose a different username.")
        return False

    # Hash the password using hashlib
    hashed_password = hash_password(password)

    try:
        # Insert username and hashed password into the database
        cur.execute("""
            INSERT INTO users (username, password_hash) VALUES (%s, %s)
        """, (username, hashed_password))
        conn.commit()
        return True

    except psycopg2.Error as e:
        # Handle database insertion error
        st.error(f"Error registering user: {e}")
        return False

# Log Login Function
def log_login(username):
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        else:
            logs = []

    except json.JSONDecodeError:
        # Handle the case when the file is empty or not containing valid JSON data
        logs = []

    logs.append({"username": username, "timestamp": str(datetime.now())})

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

    # Upload login logs data to the database
    upload_login_logs_to_postgres(logs)

    # Clear the content of the login log file after successful upload
    with open(LOG_FILE, 'w') as file:
        file.write('')

# Function to upload login logs data to PostgreSQL
def upload_login_logs_to_postgres(logs):
    try:
        for log in logs:
            cur.execute("""
                INSERT INTO login_logs (username, timestamp)
                VALUES (%s, %s)
            """, (
                log['username'], log['timestamp']
            ))
        conn.commit()
        st.success("Login logs data uploaded successfully!")

    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error uploading login logs data: {error}")

#############################################################################Json Conventor and postgresDB######################################################################

# Function to separate and save data to JSON file
def separate_and_save_to_json(files, select_option, selected_values):
    key_order = ['millname', 'machine_number_id', 'roll_id', 'revolution', 'cam', 'Date', 'Hours', 'mins', 'seconds', 'angle', 'timestamp']
    all_data = []

    for uploaded_file in files:
        with uploaded_file:
            json_data = json.load(uploaded_file)
            imagePath = json_data.get("imagePath", "")
            image_info = imagePath.split('_')

            print("Image Info:", image_info)  # Print image_info for debugging

            if len(image_info) >= len(key_order):
                data_dict = dict(zip(key_order, image_info))

                timestamp = f"{data_dict['Date']}_{data_dict['Hours']}_{data_dict['mins']}-{data_dict['seconds']}"  # Joining the date, hour, min, sec, to form timestamp
                data_dict['timestamp'] = datetime.strptime(timestamp, "%Y-%m-%d_%H_%M-%S-%f").strftime("%Y-%m-%d %H:%M:%S.%f")

                data_dict.pop('Date', None)  # Removing the keys after forming timestamp
                data_dict.pop('Hours', None)
                data_dict.pop('mins', None)
                data_dict.pop('seconds', None)
                data_dict = {**data_dict, 'angle': data_dict.pop('angle'), 'timestamp': data_dict['timestamp']}  # Reorder the data dictionary so that 'timestamp' comes before 'angle'

                data_dict['Data_model'] = select_option

                # Add selected dropdown values to data_dict
                data_dict.update(selected_values)

                all_data.append(data_dict)
            else:
                print("Invalid imagePath format:", imagePath)

    with open('parsed_data.json', 'w') as f:
        json.dump(all_data, f, indent=4)

    st.success("Data from all files separated and saved as a single JSON file.")

def create_table(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Annotation_details (
                millname VARCHAR(50),
                machine_number_id VARCHAR(50),
                roll_id VARCHAR(50),
                revolution INT,
                cam VARCHAR(50),
                angle INT,
                timestamp TIMESTAMP,
                Data_model VARCHAR(50),
                unitname VARCHAR(50),
                machine_brand VARCHAR(50),
                machine_types VARCHAR(50),
                Machine_dia VARCHAR(50),
                knit_type VARCHAR(50),
                fabric_material VARCHAR(50),
                counts VARCHAR(50),
                deniers VARCHAR(50),
                colours VARCHAR(50),
                fabric_rolling_type VARCHAR(50),
                background BOOLEAN,
                machine_gauges VARCHAR(50),
                needle_drop BOOLEAN,
                cam_type VARCHAR(50),
                lens_type VARCHAR(50)
            );
        """)
        conn.commit()
        st.success("Table created successfully!")
    except psycopg2.Error as e:
        st.error(f"Error creating table: {e}")

# Function to upload data to PostgreSQL
def upload_data_to_postgres(json_file_path):
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
            for row in data:
                cur.execute("""
                    INSERT INTO annotation_details (millname, machine_number_id, roll_id, revolution, cam, timestamp, angle, Data_model, 
                        unitname, machine_brand, machine_types, Machine_dia, knit_type, fabric_material, 
                        counts, deniers, colours, fabric_rolling_type, background, machine_gauges, 
                        needle_drop, cam_type, lens_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row['millname'], row['machine_number_id'], row['roll_id'], row['revolution'], row['cam'], 
                    row['timestamp'], row['angle'], row['Data_model'], row['unitname'], row['machine_brand'], 
                    row['machine_types'], row['Machine_dia'], row['knit_type'], row['fabric_material'], row['counts'], 
                    row['deniers'], row['colours'], row['fabric_rolling_type'], row['background'], row['machine_gauges'], 
                    row['needle_drop'], row['cam_type'], row['lens_type']
                ))
        conn.commit()
        st.success("Data uploaded successfully!")

        # Clear the content of the JSON file after successful upload
        with open(json_file_path, 'w') as file:
            file.write('')
            st.success("Data file cleared successfully!")

    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error uploading data: {error}")

# Function to hash a password using hashlib
def hash_password(password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password

# Streamlit app
def main():

    st.sidebar.title("Navigation")

    page = st.sidebar.radio("", ["Register", "Login", "JSON Converter", "Upload to DB"])

    if page == "Register":
        st.title("Register Page")
        new_username = st.text_input("New Username", placeholder="Username",label_visibility="hidden")
        new_password = st.text_input("New Password", type="password", placeholder="Password",label_visibility="hidden")
        if st.button("Register"):
            if register(new_username, new_password):
                st.success("Registration successful! You can now login.")
            else:
                st.error("Registration failed. Please try again.")

    elif page == "Login":
        st.title("Login Page")
        username = st.text_input("Username", placeholder="Username",label_visibility="hidden")
        password = st.text_input("Password", type="password", placeholder="Password",label_visibility="hidden")
        if st.button("Login"):
            if login(username, password):
                st.success("Login successful!")
                log_login(username)
                st.session_state['logged_in'] = True  # Store login status in session state
            else:
                st.error("Invalid username or password. Please try again.")

    elif not st.session_state.get('logged_in'):  # Check if user is not logged in
        st.error("You must login first.")
        return

    elif page == "JSON Converter":
        st.title("JSON Converter")
        select_option = st.selectbox("Select an option", ["None", "MDA", "FDA"])
        st.write("You selected:", select_option)

        dropdown_data = {
            "unitname": ["1", "2", "3"],
            "machine_brand": ["pailang", "mayer", "terrot", "hongji", "santoni", "fukuhara", "hisar", "Jacquard"],
            "machine_types": ["single_jersey", "double_jersey", "Jacquard"],
            "Machine_dia": ["28", "30", "32", "34"],
            "knit_type": ["plain", "rib", "interlock", "purl", "Jacquard"],
            "fabric_material": ["cotton", "cotton_polyester", "lycra_cotton", "lycra_modal_cotton", "viscose_cotton", "lycra_polyester", "lycra_tensile_cotton", "lycra_polyester_cotton"],
            "counts": ["16s", "18s", "20s", "24s", "28s", "30s", "32s", "34s", "36s", "38s", "40s"],
            "deniers": ["16", "18", "20", "24", "28", "30", "32", "34", "36", "38", "40"],
            "colours": ["grey", "melange", "white", "black", "brown", "green", "blue", "pattern"],
            "fabric_rolling_type": ["tubular", "openwidth"],
            "background": ["true", "false"],
            "machine_gauges": ["18", "20", "22", "24", "26", "28", "30", "32", "34", "36", "38", "40", "42", "44", "46"],
            "needle_drop": ["true", "false"],
            "cam_type": ["voltcam", "blackcam", "picam"],
            "lens_type": ["5mm", "default"]
        }

        selected_values = {}
        for key, values in dropdown_data.items():
            selected_value = st.selectbox(f"Select {key}", values)
            selected_values[key] = selected_value
            st.write(f"You selected {key}: {selected_value}")

        uploaded_files = st.file_uploader("Upload folder (multiple files)", accept_multiple_files=True, type="json")

        if uploaded_files is not None:
            separate_and_save_to_json(uploaded_files, select_option, selected_values)

    elif page == "Upload to DB":
        st.title("Data Upload to PostgreSQL")

        if st.button("Upload Data"):
            upload_data_to_postgres(PARSED_FILE)  # Pass the path to PARSED_FILE

if __name__ == "__main__":
    main()
