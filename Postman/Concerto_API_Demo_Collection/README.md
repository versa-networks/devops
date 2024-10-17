## Concerto API Demo - Postman Collection / Environment
    - Tested in Concerto 11.1, 11.3
    - Tested in Postman 10.5.2

## Prerequisites 
  - Import Collection and Environment into Postman.
  - Reachability to Concerto is required.
  - Update environment with the following:
        - concerto url
        - client_id, client_secret
        - username, password
        - all other variables are populated by API calls. 

## Executing the Postman Collection
  - Ensure to run OAuth getAccessToken.  Utilized for authorization of additional API calls.
  - UUIDs besides tenant_uuid included in API calls (mostly PUT, some POST/DELETE) must be updated in url and/or body based on previous API Calls.
  - Example responses included in all API calls for reference.


## Author Information
------------------

Kyle Murray - Versa Networks
