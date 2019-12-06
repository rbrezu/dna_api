## Overview

Simple implementation of a nucletide/protein datastore, you can upload a FASTA file.

Supports simple querying by text in tags and in name and also shows suggestions of similar
sequences sorted by edit distance.
It is easier to see it in smaller sized sequences 50-400bp.

For edit distance queries I used a bk-tree index.

It also supports a simple CRUD with custom queries. 

The current boilerplate code could be extended to a full fledged production code
by adding redux and redux-saga on the front and by adding authentication and authorization
on the back-end.

Also adding the index as a separate service and partitioning it based on DNA seq length and
finding a solution for streaming saving/loading of the index (implementing a custom serialization)

The python server is built on Tornado with Pymotor as a database driver.  
The front is built using barebone ReactJS.

# Running on docker

You can run the application as a docker container.  
An image is already created on dockerhub **whitesoft/dna_api**.

The same sample application is available on my server at:  
https://dna.whitesoftware.ro


```bash
docker-compose up -d
``` 

# Running on personal machine

### Prerequsite
* Install node.js
* Install Python > 3.5

## Install
```bash
yarn install
```
```bash
python install -r requirements.txt
```

## Run as dev

To start the server

```bash
> python start.py

usage: start.py [-h] [-p PORT] [-i IP] [-f FD] [-c CONF] [-l LOG_LEVEL]
                [-a APP] [-d]

Server

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  The port to run this server instance at [default:
                        8888].
  -i IP, --ip IP        The host address to run this server instance at
                        [default: 0.0.0.0].
  -f FD, --fd FD        The file descriptor number or path to listen for
                        connections on (--port and --ip will be ignored if
                        this is set)[default: None].
  -c CONF, --conf CONF  The path of the configuration file to use for this
                        server instance [default: None].
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        The log level to be used. Possible values are: debug,
                        info, warning, error, critical or notset. [default:
                        warning].
  -a APP, --app APP     A custom app to use for this server in case you
                        subclassed [default: server.app.LandmarkServiceApp].
  -d, --debug           Debug mode [default: False].
```

To start the frontend

```bash
yarn start
```

By default the application will be available on localhost:8888


### Application structure

```
.
├── dist                 # bundled js files and html
├── public               # index.html and other templates
├── scripts              # script to populate mongodb
├── server               # python source code folder
├── web                  # reactjs front
├── docker-compose.yml   # docker compose file 
├── Dockerfile
├── application.conf     # conf file for the python server
├── start.py             # start file for the app
├── webpack.*.js         # webpack config for dev/prod
...
```

### Python
```
.
├── handlers             # web request handlers
├── model                # repository and object model code
├── index                # pybktree index class 
├── app.py               # application server class that defines all routes
├── config.py            # config parser
├── console.py           # console args parser
├── context.py           # application request context class
├── importer.py          # helper for dynamic module import from config
├── json_encoder.py      # json encoder with ObjectId and datetime support
├── utils.py             # various utils (ex. Singleton metaclass) 
```

### React JS
```
.
├── component            # application components
├── views                # application views (Sequence and Upload)
├── history.js           # browser history 
├── index.js             
```
