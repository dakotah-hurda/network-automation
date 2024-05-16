# Use the base Python image
FROM python:3.12.3-bookworm

# Set the working directory inside the container
WORKDIR /home/runneradmin/actions-runner/_work/network-automation/network-automation

# Copy the requirements.txt file from your host to the container, then install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy trusted-ssl-certs file from your host to the container, then add them to Certifi lib
COPY data/trusted-ssl-certs data/trusted-ssl-certs
RUN cat data/trusted-ssl-certs >> /usr/local/lib/python3.12/site-packages/certifi/cacert.pem