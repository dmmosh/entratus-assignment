import requests

response = requests.post("http://localhost:8080/conversations")
print(response.text)
response = response.json()
id = response['id']

messages = [
    'Hello Claude I am interested in stock prices.',
    'AAPL Ticker',
    'Overall percent change',
    'In the last week'
]

messages2 = [
    'Hello Clause show me the AAPL Ticker percent price change in the last week.'
]


for message in messages:
    print()
    print('user:\t',message)
    print()
    response = requests.post(
        f"http://localhost:8080/conversations/{id}/messages",
        headers={
            "content-type": "application/json"
        },
        json={
            "message":message
        }
    )
    print('assistant:\t',response.json()['message'])


print()
response = requests.get(
        f"http://localhost:8080/conversations/{id}",
    )
print('conv_logs:\n',response.text)

print()
response = requests.get(
        f"http://localhost:8080/conversations/{id}/usage",
    )
print('conv_logs:\n',response.text)