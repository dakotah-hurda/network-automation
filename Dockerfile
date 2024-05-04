# Uses the official Ubuntu container image. 
# This can be modified to pull a customized image from our local private repo.
FROM ubuntu:latest

# Sets an arbitary workspace for this Dockerfile.
WORKDIR /usr/src/app

# Chance here to scan the image with security scans before loading anything else on it. 

# Runs CLI to update the OS and install Python/Pip
# This can get wrapped up in the image on our private repo instead of pulling it live at build-time
RUN apt-get update && apt-get install -y python3 python3-pip 

# Uses pip to install all requirements listed in the requirements.txt file
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Chance here to scan imported modules with security scans.

# Copies rest of entire repo code into the container
COPY . .

# Runs this command, then closes the container. 

# CMD [ "python3", "./src/base_compliancy.py"]
