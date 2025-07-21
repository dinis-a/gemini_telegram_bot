FROM python:3.12-slim

WORKDIR /app

RUN mkdir -p /app/logs

# Copy application files
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Make the scripts executable
RUN chmod +x ./start_script.sh

# Define the command to run the application
CMD ["./start_script.sh"]