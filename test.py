import requests


def send_msg(messages:list, extra_args:dict = {}):
    response = requests.post("http://0.0.0.0:8080/conversations")
    print(response.text)
    response = response.json()
    id = response['id']
    for message in messages:
        print()
        print('USER:\t',message)
        print()
        response = requests.post(
            f"http://0.0.0.0:8080/conversations/{id}/messages",
            headers={
                "content-type": "application/json"
            },
            json={
                "message":message
            } | extra_args
        )
        print(response.status_code, 'ASSISTANT:\t',end='')
        if(response.status_code == 200):
            print(response.json()['message'])

    
    print()

    # response = requests.get(
    #         f"http://0.0.0.0:8080/conversations/{id}",
    #     )
    # print('CONV LOGS:\t',response.json())

    # print()
    # response = requests.get(
    #         f"http://0.0.0.0:8080/conversations/{id}/usage",
    #     )
    # print('USAGE:\t',response.json())
    # print()

    

messages_handoff1 = [
    'Hello Claude I am interested in stock prices.',
    'AAPL Ticker',
    'Overall percent change',
    'In the last day'
]
messages_handoff2 =[
    'I am interested in MSFT Ticker prices.',
    'The closing prices',
    'META Ticker closing prices over the past 5 trading days'
]

messages_static = [
    'I would like GOOGL prices'
]

messages_error = {
    ''
}

print('------------------------------------------------------')
send_msg(messages_handoff1) # test case 1
print('------------------------------------------------------')
send_msg(messages_handoff2) # test case 2
print('------------------------------------------------------')
send_msg(messages_static, {'is_static':True, 'tools_static':['callSpecialist']}) # static test
print('------------------------------------------------------')
send_msg(messages_error) # error case 4
print('------------------------------------------------------')





