import streamlit as st
import paramiko
import os

def fetch_data_server(server_ip, username, password, server_path):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the server
        ssh.connect(hostname=server_ip, username=username, password=password)

        # Open an SFTP session
        sftp = ssh.open_sftp()

        # List files in the server directory
        files = sftp.listdir(server_path)

        # Close the SFTP session
        sftp.close()

        # Close the SSH connection
        ssh.close()

        return files

    except paramiko.AuthenticationException:
        st.error("Authentication failed. Please check your credentials.")
    except paramiko.SSHException as ssh_exception:
        st.error(f"SSH error: {ssh_exception}")

def download_data_from_server(server_ip, username, password, server_path, output_dir):
    file_names = fetch_data_server(server_ip, username, password, server_path)
    if file_names:
        try:
            os.makedirs(output_dir, exist_ok=True)
            for file_name in file_names:
                with open(os.path.join(output_dir, file_name), "wb") as f:
                    with paramiko.SSHClient() as ssh:
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect(server_ip, username=username, password=password)
                        with ssh.open_sftp() as sftp:
                            file_path = f"{server_path}/{file_name}"
                            sftp.get(file_path, os.path.join(output_dir, file_name))
            st.success(f"Data downloaded to: {output_dir}")
        except Exception as e:
            st.error(f"Error saving data: {e}")
    else:
        st.warning("No data fetched.")

def upload_data_to_server(server_ip, username, password, server_path, uploaded_files):
    try:
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(server_ip, username=username, password=password)
            with ssh.open_sftp() as sftp:
                for uploaded_file in uploaded_files:
                    with sftp.file(f"{server_path}/{uploaded_file.name}", 'wb') as file:
                        file.write(uploaded_file.getvalue())
        st.success(f"Files uploaded to: {server_path}")
    except paramiko.AuthenticationException:
        st.error("Authentication failed. Please check your credentials.")
    except paramiko.SSHException as ssh_exception:
        st.error(f"SSH error: {ssh_exception}")
    except Exception as e:
        st.error(f"Error uploading files: {e}")

def main():
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    # Login Page
    if not st.session_state.logged_in:
        st.title("Login Page")
        username = st.text_input("Username", placeholder="Username")
        password = st.text_input("Password", type="password", placeholder="Password")
        if st.button("Login"):
            if username == "edgecam" and password == "Charlemagne@1":  # Replace with actual authentication logic
                st.session_state.logged_in = True
                st.success("Login successful!")
                display_main_page()
            else:
                st.error("Invalid username or password. Please try again.")
    else:
        display_main_page()

def display_main_page():
    # Main Page
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select an option", ["Download", "Upload"])
    
    if page == "Download":
        st.header("Download Data from Server")
        # Input field for server credentials and path
        server_ip = '169.254.0.2'
        username = 'edgecam'
        password = 'Charlemagne@1'
        server_path = '/home/edgecam/projects'
        # Input field for output directory
        output_dir = st.text_input("Output Directory:")
        # Button to fetch data from the server
        if st.button("Fetch Data"):
            download_data_from_server(server_ip, username, password, server_path, output_dir)
    elif page == "Upload":
        st.header("Upload Data to Server")
        # Input field for server credentials and path
        server_ip = '169.254.0.2'
        username = 'edgecam'
        password = 'Charlemagne@1'
        server_path = '/home/edgecam/uploaded_data'
        # File uploader for multiple files
        uploaded_files = st.file_uploader("Upload Files:", type=['csv', 'txt', 'json'], accept_multiple_files=True)
        # Button to upload data to the server
        if st.button("Upload"):
            if uploaded_files:
                upload_data_to_server(server_ip, username, password, server_path, uploaded_files)
            else:
                st.warning("Please select files to upload.")

if __name__ == "__main__":
    main()
