import streamlit as st
import json
from datetime import datetime, timedelta,timezone
import psycopg2
import os
import requests
# import hashlib

######################################################################LOGIN PAGE ##################################################################################

# Database connection
conn = psycopg2.connect(
    database="knitting",
    user="postgres",
    password="55555",
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
# def user_exists(username, password):
#     cur.execute("SELECT username FROM users WHERE username = %s AND password_hash = %s", (username, hash_password(password)))
#     return cur.fetchone() is not None


# Login Function
# Login Function
def login(username, password):
    # Retrieve the password from the database based on the username
    cur.execute("SELECT password FROM users WHERE username = %s", (username,))
    stored_password = cur.fetchone()
    
    if stored_password:
        # Check if the provided password matches the stored password
        if password == stored_password[0]:
            return True
    return False



# # Registration Function
# def register(username, password):
#     # Check if the user already exists
#     if user_exists(username):
#         st.error("User already exists. Please choose a different username.")
#         return False

#     # Hash the password using hashlib
#     hashed_password = hash_password(password)

#     try:
#         # Insert username and hashed password into the database
#         cur.execute("""
#             INSERT INTO users (username, password_hash) VALUES (%s, %s)
#         """, (username, hashed_password))
#         conn.commit()
#         return True

#     except psycopg2.Error as e:
#         # Handle database insertion error
#         st.error(f"Error registering user: {e}")
#         return False

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
        

# Function to save files to the Docker volume from a specified directory
def save_to_volume_from_directory(directory_path):
    files = os.listdir(directory_path)
    for file_name in files:
        file_path = os.path.join(directory_path, file_name)
        with open(file_path, "rb") as file:
            file_content = file.read()
        
        # Define the path where the file will be saved in the Docker volume
        save_path_volume = os.path.join("/app/data", file_name)

        # Save the file to the Docker volume
        with open(save_path_volume, "wb") as f:
            f.write(file_content)

# Trigger Airflow DAG function
def trigger_airflow_dag():
    airflow_dag_url = "http://airflow-webserver:8080/api/v1/dags/send_nas/dagRuns"
    
    # Set execution date to current time plus one minute
    execution_date = datetime.now(timezone.utc) + timedelta(minutes=1)
    payload = {
        "conf": {},
        "execution_date": execution_date.isoformat()  # Set execution date to one minute in the future
    }
    try:
        response = requests.post(airflow_dag_url, json=payload)
        response.raise_for_status()
        st.success("Airflow DAG triggered successfully!")
    except Exception as e:
        st.error(f"Error triggering Airflow DAG: {e}")

def separate_and_upload_to_postgres(files, select_option, selected_values):
    key_order = ['millname', 'machine_number_id', 'roll_id', 'revolution', 'cam', 'Date', 'Hours', 'mins', 'seconds', 'angle', 'timestamp']

    for uploaded_file in files:
        with uploaded_file:
            json_data = json.load(uploaded_file)
            imagePath = json_data.get("imagePath", "")
            image_info = imagePath.split('_')
            print("Image Info:", image_info)  

            if len(image_info) >= len(key_order):
                data_dict = dict(zip(key_order, image_info))

                timestamp = f"{data_dict['Date']}_{data_dict['Hours']}_{data_dict['mins']}-{data_dict['seconds']}"
                data_dict['timestamp'] = datetime.strptime(timestamp, "%Y-%m-%d_%H_%M-%S-%f").strftime("%Y-%m-%d %H:%M:%S.%f")

                data_dict.pop('Date', None)  
                data_dict.pop('Hours', None)
                data_dict.pop('mins', None)
                data_dict.pop('seconds', None)
                data_dict = {**data_dict, 'angle': data_dict.pop('angle'), 'timestamp': data_dict['timestamp']}

                data_dict['Data_model'] = select_option

                # Add selected dropdown values to data_dict
                data_dict.update(selected_values)

                try:
                    cur.execute("""
                        INSERT INTO annotation_details (millname, machine_number_id, roll_id, revolution, cam, timestamp, angle, Data_model, 
                            unitname, machine_brand, machine_types, Machine_dia, knit_type, fabric_material, 
                            counts, deniers, colours, fabric_rolling_type, background, machine_gauges, 
                            needle_drop, cam_type, lens_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data_dict['millname'], data_dict['machine_number_id'], data_dict['roll_id'], data_dict['revolution'], data_dict['cam'], 
                        data_dict['timestamp'], data_dict['angle'], data_dict['Data_model'], data_dict['unitname'], data_dict['machine_brand'], 
                        data_dict['machine_types'], data_dict['Machine_dia'], data_dict['knit_type'], data_dict['fabric_material'], data_dict['counts'], 
                        data_dict['deniers'], data_dict['colours'], data_dict['fabric_rolling_type'], data_dict['background'], data_dict['machine_gauges'], 
                        data_dict['needle_drop'], data_dict['cam_type'], data_dict['lens_type']
                    ))
                    conn.commit()
                    st.session_state['upload_successful'] = True  # Set upload_successful state to True

                except (Exception, psycopg2.DatabaseError) as error:
                    st.error(f"Error uploading data: {error}")


# Function to create annotation_details table if not exists
def create_annotation_details_table(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS annotation_details (
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
    except psycopg2.Error as e:
        st.error(f"Error creating table: {e}")

create_annotation_details_table(conn)

# Function to check if the table exists
def table_exists(table_name):
    cur.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')")
    return cur.fetchone()[0]

# Function to upload data to PostgreSQL
def upload_data_to_postgres(json_file_path):
    if not table_exists("annotation_details"):
        create_annotation_details_table(conn)  # Create the table if it doesn't exist

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

    except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()  # Rollback the transaction in case of an error
        st.error(f"Error uploading data: {error}")
# Function to hash a password using hashlib
# def hash_password(password):
#     hashed_password = hashlib.sha256(password.encode()).hexdigest()
#     return hashed_password

def main():

    st.sidebar.title("Navigation")

    page = st.sidebar.radio("", [ "Login", "JSON Converter"])

    # if page == "Register":
    #     st.title("Register Page")
    #     new_username = st.text_input("New Username", placeholder="Username",label_visibility="hidden")
    #     new_password = st.text_input("New Password", type="password", placeholder="Password",label_visibility="hidden")
    #     if st.button("Register"):
    #         if register(new_username, new_password):
    #             st.success("Registration successful! You can now login.")
    #         else:
    #             st.error("Registration failed. Please try again.")

    if page == "Login":
        st.title("Login Page")
        username = st.text_input("Username", placeholder="Username",label_visibility="hidden")
        password = st.text_input("Password", type="password", placeholder="Password",label_visibility="hidden")
        if st.button("Login"):
            if login(username, password):
                st.success("Login successful!")
                log_login(username)
                st.session_state['logged_in'] = True  
            else:
                st.error("Invalid username or password. Please try again.")

    elif not st.session_state.get('logged_in'): 
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
          separate_and_upload_to_postgres(uploaded_files, select_option, selected_values)
        temp_directory = "/path/to/temporary/directory"
        for uploaded_file in uploaded_files:
                with open(os.path.join(temp_directory, uploaded_file.name), "wb") as file:
                    file.write(uploaded_file.getvalue())
        save_to_volume_from_directory(temp_directory)
        if st.session_state.get('upload_successful'):
         st.success("Data uploaded successfully!")
        uploaded_files.clear()
        st.session_state['upload_successful'] = False

    # Trigger Airflow DAG button
        if st.button("Send Data to Nas"):
           trigger_airflow_dag()

if __name__ == "__main__":
    main()

