# Mega CNC
Software for controlling megacell charger lithium cell testing devices

# Deploying the App on Ubuntu with Docker Compose
This guide walks you through deploying the app on an Ubuntu instance using Docker Compose, providing a straightforward way to get the app up and running.
- I tested successfully the build and run process in Virtual Box VM and should work on any virtualized environment or barebone Server or PC
- I tested also on RPI 4 4GB RAM with 32 GB SD Card and the app runs well



## Prerequisites
Ubuntu Desktop 22 (or the latest version)
Internet connection
Step 1: Set Up Ubuntu
Install the latest version of Ubuntu Desktop on a virtual machine (VM) or a physical machine as per your preference.

## Step 2: Install Docker and Docker Compose
Update your package lists and install Docker and Docker Compose using the following commands:
```
sudo apt update
sudo apt install docker.io -y
sudo apt install docker-compose
```

## Step 3: Clone the Repository
Install Git, clone the repository, and navigate to the project directory:
```
sudo apt install git
cd ~
git clone https://github.com/alex3dbros/megacnc.git
cd megacnc
```

## Step 4: Build and Launch the App
Build the Docker images and launch the app for the first time with Docker Compose:
```
sudo docker-compose up --build
```

## Step 5: Initialize the Database
While the app is running, open a new terminal to initialize the database. First, check the running containers:
```
sudo docker ps
```

Look for a container named megacnc_web_1. Then, execute the following commands to make and apply database migrations:
```
sudo docker exec megacnc_web_1 python manage.py makemigrations
sudo docker exec megacnc_web_1 python manage.py migrate
```

## Step 6: Access the App
Return to the terminal where Docker Compose is running, press CTRL+C to stop the containers, and then restart them:
```
sudo docker-compose up
```

Your app should now be accessible on the VM. Open a web browser and navigate to http://<VM_IP_ADDRESS>:8000, replacing <VM_IP_ADDRESS> with your VM's actual IP address (e.g., http://192.168.1.127:8000).




# Update procedure

## To facilitate the update, you can run the following commands

```
cd megacnc
git pull
sudo docker-compose down
sudo docker-compose up --build
```

## It's a good idea to run the migration commands in case there are new changes in Db
```
sudo docker exec megacnc_web_1 python manage.py makemigrations
sudo docker exec megacnc_web_1 python manage.py migrate
```

## If it fails to do the migrations because of conflicts, run the following command for makemigrations

```
sudo docker exec -it megacnc_web_1 sh -c "echo 'y' | python manage.py makemigrations --merge"
```


# Support and donations are welcome

### Stripe:
https://buy.stripe.com/8wMdUmaZ00mc67m4gk

### Paypal:
https://www.paypal.com/donate/?hosted_button_id=B8Z5L9NE86KLC