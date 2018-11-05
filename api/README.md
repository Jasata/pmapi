# PATE Monitor JSON REST API

This API implementation offers all the functionality that is required to meet usage specification and supply the web UI with data and command channel.

## Basic Terminology

**URI parameters** are baked into the resource path. For example; ''/api/company/123/order/90121'' has two URI parameters. The ID of the company entity (123) and the ID of the order (90121).

**Query parameters** are appended to the URI with '?' character and chained with '&' separator. For example; ''/api/classifieddata?begin=1541409470&fields=ss00p01,ss00p02'' has two query parameters; ''begin'', which is an UNIT timestamp in string format and ''fields'', which is a string that can be converted into a comma separated list.

**Payload parameters** are located in the HTTP payload portion, in JSON format (as far as this API specification is concerned). Usage of Payload parameters is reserved to data altering actions, such as PUT,PATCH and POST, which need to deliver number of entity attributes. Notable exception is the DELETE HTTP method, which does not need to send entity data and identifies the target for the delete operation through URI parameter.

**Header parameters** are located in the HTTP header. Aside from path/endpoint, HTTP method and response codes, these parameters have no other in the API specification and are left for HTTP and application purposes (such as session management, XSS prevention and access control mechanisms). 

### There exists two distinct GET requests

First, the obvious, can be called as the "fetch" type. These GET requests identify the entity with an ID and responses return it as one object. Second type can be called "search" type, which can define any number of criteria that result in zero or more matching entities.

The distinction between these is relevant, because "fetch" type entity requests are supposed to be identified by means of *URI parameters* and because search parameters are to be sent as *query parameters*. Also, "fetch" API endpoints do not support search criterias (usually, only a field selector query paramter).

When "fetch" yields no results, response "404 Not Found" is returned. When "search" type request yields no results, an empty list is returned with code "200 OK".

### Endpoints are either Entity generic or Identified Entities

While most CRUD actions deal with identified entities ('/api/entity/<int:id>'), POST ("create") action cannot. Only the service can give the new entity instance a valid and non-conflicting ID. GET ("read") action can be either to identified entity (making it "fetch" type), or to entity generic (making it a "search" request).

For this reason, identified routes ('/api/entity/<int:id>') and generic routes ('/api/entity') are usually defined separately and offer different sets of supported methods.

## REST API Principles

This implementation follows number of principles.

  * Use (singular) nouns in URIs to name resources. (no verbs, no plurals…)
  * Specific entity access identifies the target through URI parameter(s): ''/api/v1/employee/4121/reservation/1412/''.
  * Meta parameters, such as field selector (specifying which fields are returned), are sent
 as query parameters (…?fields=firstname,lastname&order=asc)
  * Both GET request types ("fetch" and "search") accept all parameters as query parameters.
  * Require all entity data in JSON payload for non-idempotent (state altering) methods (POST,PUT,PATCH).
  * DELETE method does not use JSON payloads. Entity is identified by URI parameter (‘/user/<id>’).
  * Authentication (keys, cookies, tokens, whatever) shall not use any other storage than the HTTP header.
  * When supporting versions, recommended way is to build that into the endpoint URI: (‘/api/v2/user’). This allows supporting multiple versions and very simple interface of obsoleted API versions – they simply are not found. No code to write about “wrong version requested”…
  * "Fetch" type requests are served only via URI parametrized endpoints ('/api/v1/employee/<id>'), "search" type requests shall not be accessible through endpoints that have parametrized the identity of the searched entity. (Correct would be; '/api/v1/employee/').

## HTTP Methods

    GET     get/query
    POST    create new
    PUT     NOT USED
    PATCH   update existing
    DELETE  delete

NOTE: Some specifications make the distinction between PUT and PATCH to be that PUT *replaces* the specified entity, while PATCH *updates* the existing entity. This API has no use for such distinction and PUT method is unused

## HTTP Responses

This section discusses HTTP responses in general terms. Implementation strives to follow these principles whereever possible.

        +-------------+---------+--------+---------+--------+--------+
        | Resource    | POST    | GET    | PUT     | PATCH  | DELETE |
        +-------------+---------+--------+---------+--------+--------+
        | /user	      | Create  | Search | 405     | 405    | 405    |
        | /user/<:id> | 405     | Fetch  | Replace | Update | Delete |
        +-------------+---------+--------+---------+--------+--------+

Reply "405 Method Not Allowed" should be the only 4xx response used. Response "406 Not Acceptable" should indicate that while the combination of an endpoint and HTTP method is allowed, something in the request and/or its arguments make the action disallowed.

### GET (entity generic endpoint)

Action: Search  
Payload: None  
URI parameters: None

**Possible Replies**

        Code                    Payload                 Description
        200 OK                  'data': [{},...]        Success. List of objects (0...N) returned.
        401 Unauthorized        None                    Access/authorization error.
        405 Method not allowed  None                    Endpoint + method combo not supported.
        406 Not Acceptable      None                    Argument error.

### GET (identified entity endpoint)

Action: Fetch  
Payload: None  
URI parameters: <int:id>

**Possible Replies**

        Code                    Payload                 Description
        200 OK                  'data': {}              Success. Object is returned.
        401 Unauthorized        None                    Access/authorization error.
        404 Not Found           None                    Entity by ID not found.
        405 Method not allowed  None                    Endpoint + method combo not supported.
        406 Not Acceptable      None                    Argument error.

### POST (entity generic endpoint)

Action: Create  
Payload: Entity object JSON  
URI parameters: None

**Possible Replies**

        Code                    Payload                 Description
        200 OK                  'data': {}              Success. Object is returned.
        401 Unauthorized        None                    Access/authorization error.
        405 Method not allowed  None                    Endpoint + method combo not supported.
        406 Not Acceptable      None                    Argument error or DB CHECK constraint failure.
        409 Conflict            None                    Unique, Primary key or Foreign key violation.

The rationaly for "200 OK" to return the whole object is that entities commonly get additional attributes and/or have submitted attributes altered. They also gain the ID value, which is relevant for the client solution.

### PUT (identified entity endpoint)

This API does not use *replace* operations. "405 Method Not Allowed" is returned.

### PATCH (identified entity endpoint)

Action: Update  
Payload: Entity object (with only the attributes to be updated)  
URI parameters: <int:id>

**Possible Replies**

        Code                    Payload                 Description
        200 OK                  'data': {}              Success. Object is returned.
        401 Unauthorized        None                    Access/authorization error.
        404 Not Found           None                    Entity by ID not found.
        405 Method not allowed  None                    Endpoint + method combo not supported.
        406 Not Acceptable      None                    Argument error or DB CHECK constraint failure.
        409 Conflict            None                    Unique, Primary key or Foreign key violation.

### DELETE (identified entity endpoint)

Action: Delete  
Payload: None  
URI parameters: <int:id>

**Possible Replies**

        Code                    Payload                 Description
        200 OK                  None                    Success.
        401 Unauthorized        None                    Access/authorization error.
        404 Not Found           None                    Entity by ID not found.
        405 Method not allowed  None                    Endpoint + method combo not supported.
        409 Conflict            None                    Foreign key violation.


