# Use the official Python image as the base image
FROM ubuntu:latest

# Set the working directory inside the container
WORKDIR /app


# Copy the application code into the container
COPY homepage.py /app/
COPY Home/ app/ 
COPY add_users.py /app/
COPY login_logs.json /app/


# # Define environment variables for PostgreSQL
# ENV POSTGRES_HOST=localhost
# ENV POSTGRES_PORT=5432
# ENV POSTGRES_USER=postgres
# ENV POSTGRES_PASSWORD=vishnu123
# ENV POSTGRES_DB=naserver
RUN apt-get update 


# Install Python dependencies
RUN pip3 install -r requirements.txt


# Expose the port that Streamlit listens on
EXPOSE 8501

# Mount volume for data exchange
VOLUME /app/data
# Command to run Streamlit app
#CMD ["streamlit", "run", "--server.port", "8501", "homepage.py"]
