import requests

response = requests.post("http://localhost:8080/conversations")
print(response.text)
response = response.json()
id = response['id']

messages = [
    'Hello Claude I am interested in stock prices.',
    'AAPL Ticker',
    'Overall percent change',
    'In the last day'
]
messages2 =[
    'I am interested in MSFT Ticker prices.',
    'The closing prices',
    'META Ticker closing prices over the past 5 trading days'
]

messages3 = [
    'Hello Clause show me the AAPL Ticker percent price change in the last week.'
]


for message in messages2:
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