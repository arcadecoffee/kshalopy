import requests

id_token = input("ID Token: ")

session = requests.Session()

# As found in AWS Appsync under Settings for your endpoint.
APPSYNC_API_ENDPOINT_URL = (
    "https://mnlxsdywfvhoxh627qfakupckm.appsync-api.us-east-1.amazonaws.com/graphql"
)

# Use JSON format string for the query. It does not need reformatting.
query = """
    query foo {
        getUserDevices {
           deviceid devicename devicestatus
        }
    }
"""

# Now we can simply post the request...
response = session.request(
    url=APPSYNC_API_ENDPOINT_URL,
    headers={"Authorization": id_token},
    method="POST",
    json={"query": query},
)
print(response.text)
