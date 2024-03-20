# Use the official Python image as the base image
FROM python

# Set the working directory inside the container
WORKDIR /app

# Copy the application code into the container
COPY homepage.py /app/

# Install any required dependencies
RUN pip install psycopg2-binary 
RUN pip install wheel
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

# Expose the port that Streamlit listens on
EXPOSE 8501

# Command to run the Streamlit application
CMD ["streamlit", "run", "homepage.py"]
