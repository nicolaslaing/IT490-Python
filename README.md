# IT490-Python
Python Flask REST service for running local RabbitMQ API

To run the barebones application:

    python app.py

There are arguments you may supply, in respective order, within this list:

    -ip <RabbitMQ IP address>
    -dmz

Example:

    python app.py -ip 127.0.0.1 -dmz

This will connect to the RabbitMQ listener on 127.0.0.1 and allow API data to be obtained through the DMZ server.

There are two local API routes that can be requested:

    0.0.0.0:5000/publish/{Queue Name}
    0.0.0.0:5000/consume/{Queue Name}

# Publish
The publish route will submit an HTTP POST request. You may supply a specific API HTTP request object if you are trying to obtain data from an outside API via the DMZ, or you may supply whatever you'd like - as long as it's in JSON format. The object is published to the running RabbitMQ server queue using the name {Queue Name}.

The DMZ will fetch API based on the following object:

    {
        "queue_to_publish: "queue",
        "api_protocol": "http", // or https
        "api_domain": "site.com", // the website domain, plus it's TLD (.com, .net, ect.), add "www." if necessary
        "api_route": "/path/to/route", // the API route
        "api_params": "param1=value&param2=value2", // as many params as GET can handle
    }

Default API values:

    {
        "queue_to_publish: "api",
        "api_protocol": "https",
        "api_domain": "secondhandsongs.com"
        "api_route": "",
        "api_params": "?format=json" // Second Hand Songs (SHS) API requires this
    }

Here is an example request:

    curl -X POST -H "Accept: application/json" -H "Content-Type: application/json" -d '{"api_route":"artist/123/performances", "queue_to_publish":"artist"}' 0.0.0.0:5000/publish/artist

# Consume
The consume route will submit an HTTP GET request. It will consume the RabbitMQ queue supplied in the route {Queue Name}. If you are running as the DMZ server, the response will contain whatever API data was published to RabbitMQ. If you are not the DMZ, it will reply with the intial HTTP request data that was published.

Here is an example request:

    curl 0.0.0.0:5000/consume/artist