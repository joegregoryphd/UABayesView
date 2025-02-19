# UA-BayesView
- This projects goal is to take an OML file that describes a bayesian network and create a visualization of it. This will also take into consideration different types of evidence input by the user. 
- This will be deployed on a server as a web application.


## SETUP (For Linux/Unix)
### Prerequisites
- Docker installed on your machine. If you do not have Docker installed, please follow the installation guide at Docker's official website: https://www.docker.com/products/docker-desktop/

### Start Docker Desktop
- Ensure Docker Desktop is running on your machine

### Clone the repository
- Use the green code button and copy the HTTPS link. Once copied run `git clone replace-with-copied-HTTPS-link` in your terminal

### Building the Docker image
- Navigate to the directory where you cloned the repository using  `CD path/to/cloned/repository`
- Once in the proper directory run the command `docker build -t ua-bayesview .`
- *Note: This will take a few minutes to run as its building the docker image*

### Running the Docker image
- In your terminal then run `docker run -d -p 8000:5000 ua-bayesview`
- In the web browser of your choice go to this link: **http://localhost:8000**
- You will now be able to access UA-BayesView

### Stopping the Docker image
- In the terminal run the command `docker ps` which will list all the docker imagaes that are running
- Identify the Container ID that corresponds to the ua-bayesview docker image
- Run the command `docker stop replace-with-container-id`


## SETUP (For Windows or people not familiar with Linux/Unix)
### Prerequisites
- Docker installed on your machine. If you do not have Docker installed, please follow the installation guide at Docker's official website: https://www.docker.com/products/docker-desktop/
- Visual Studio Code installed on your machine. If you do not have VSCode installed, please follow the installation guide at Visual Studio's official website: https://code.visualstudio.com/download

### Start Docker Desktop
- Ensure Docker Desktop is running on your machine

### Clone the repository
- Use the green code button on the GitHub code page and copy the HTTPS link
- Once copied open VScode and get to the welcome page
- Locate the clone git repository link and paste in the HTTPS link that was just coppied
- Follow the on screen prompts

### Building the Docker image
- Open the cloned repo in VSCode
- In the top left corner of VSCode open a new terminal
- In the VSCode terminal that was just opened paste this command and press the enter key: `docker build -t ua-bayesview .`
- *Note: This will take a few minutes to run as its building the docker image*

### Running the Docker image
- Open Docker Desktop and go to the Images tab on the left hand side of the application
- Under the Name column find ua-bayesview
- Click the run button on in the Actions column of the ua-bayesview image
- A pop-up will be displayed asking for "Optional settings"
- Click the drop down menu and locate the Host port input section
- Enter in **8000** into the host port section
- Click the run button
- In the web browser of your choice go to this link: **http://localhost:8000**
- You will now be able to access UA-BayesView

### Stopping the Docker image
- In Docker Desktop hit the stop button in the top right corner of the application

# UABayesView
