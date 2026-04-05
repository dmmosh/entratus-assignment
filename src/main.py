import fastapi # api
import uvicorn # server
import os # env
import random # id generation
import json # json from config file
from pydantic import BaseModel # base model for args
from typing import Optional # static testing


import yfinance as yf # yahoo finance data

from anthropic import Anthropic
from fastapi import FastAPI, HTTPException
app = FastAPI()
conversations = {}
config = None
intake = None # intake agent
specialist = None

bots_key = {} # double dict
key_bots = {}

def read_config_tools(entry_name:str): # reads config entry, returns dict which claude can understand
    if entry_name not in config:
        return []
    
    entry = config[entry_name]
    if "tools" not in entry: # BC
        return []
    

    def tool_conv(tools): # read from shared as well
        out = []
        for tool in tools:
         tool_curr = {'name':tool['name'],
                  'description':tool['callOn']+' '+tool['description']
                  }
         
         tool_curr["input_schema"] = { # default input schema
             'type':'object',
             'properties':{}
         }
         
         if('return' in tool):
            tool_curr["input_schema"]['properties'] = {"returnVal":tool['return']}
            tool_curr["input_schema"]['required'] =['returnVal']

         out.append(tool_curr)
        return out
    out = []

    for share in config['shared']: # append shared info
        if entry_name in share['between'] and 'tools' in share:
               out.extend(share['tools'])
            

    out.extend(tool_conv(entry['tools']))

    return out


def read_config_system(entry_name:str): # reads the config
    if entry_name not in config:
       return ''
    entry = config[entry_name]
    out = ''

    for share in config['shared']: # append shared info
        if(entry_name in share): 
            if 'context' in share:
             out += ' '.join(share['context'])
            if 'behavioral' in share:
              out+= ' ' + ' '.join(share['behavioral'])

    if 'context' in entry:
       out += ' '.join(entry['context']) 

    if 'behavioral' in entry:
        out += ' ' + ' '.join(entry['behavioral']) 
    

    return out

def read_config_model(entry_name:str): # reads the model to use
      
    model = ''
    for share in config['shared']: # if model in shared, get it
        if entry_name in share['between'] and 'model' in share:
            model= share['model']

    if entry_name in config and 'model' in config[entry_name]:
      model= config[entry_name]['model']

    return model
      
      # cant be a default, model is required

def read_config_temp(entry_name:str): # reads temperature (1-seriousness)
    out = 0.0
    for share in config['shared']: # if model in shared, get it
      if entry_name in share['between'] and 'seriousness' in share:
        out =  round(1.0 - float(share['seriousness']),2)

    if entry_name in config and 'seriousness' in config[entry_name]:
      out =  round(1.0- float(config[entry_name]['seriousness']),2)

    return out
      
def read_config_max_tokens(entry_name:str): # reads temperature (1-seriousness)
    out = 0
    # a claude token is roughly equal to 4 chars 
    for share in config['shared']: # if model in shared, get it
      if entry_name in share['between'] and 'avgChars' in share:
        out =  int(share['avgChars'])//4

    if entry_name in config and 'avgChars' in config[entry_name]:
      out =  int(config[entry_name]['avgChars'])//4
            
    return out
    


class conv:
    def __init__(self):
        if(len(conversations)>= 999999-100000): # bounds checking
            raise Exception('conversation limit reached')
        
        self.id = random.randint(100000,999999) # randomly generates id in 6 digit range
        while self.id in conversations: # if key exists (key smash)
            self.id = random.randint(100000,999999) # randomly generates id in 6 digit range
        
        

        conversations[self.id] = self   # adds itself to the conversations hash 
        
        self.tokens = {key:0 for key in key_bots} # makes token counts for the bots 
        self.history_handled = [] # the handled pair history pair
        self.history = [] # conv logs , formatted for claude use (so dont have to reformat)
        # each log will consist of who handled it
        # ex {'role':'user','content':'hello'}
        # ex {'role':'assistant','content':'hii'}
        
        self.i = 0 # the index of the bottom of the queue (start of current gathering period)
        # when the conversation is handled by specialist, self.i is moved to len(self.logs) , or the index of the new conversation
    

    def push_history(self,message:str,user:bool = True): # pushes to history, user is -1 key
        self.history.append({
            'role':'user' if user else 'assistant',
            'content':message
        }) # appends msg to history


    def pop_history(self,i:int=0): # pops the most recent history in a way which claude api likes, leaves i items
       self.i = len(self.history)-i # "pops" from the stack , sets i to new value
        
class agent: # calls agent class
    def __init__(self, name):
        self.name = name # stores name
        self.key = bots_key[self.name]
        self.client = Anthropic() # inits anthropic class
        self.tools = read_config_tools(name) # reads tools
        self.system = read_config_system(name) # reads system      
        self.model = read_config_model(name)
        self.temp = read_config_temp(name)
        self.tokens = read_config_max_tokens(name)
        # print(self.client,
        #       self.tools ,
        #       self.system,
        #       self.model ,
        #       self.temp,
        #       self.tokens, sep='\n\n')
    def respond(self, id:int, context:str=''): # response wrapper
        #note: the requests count is handled
        return  self.client.messages.create(
            model = self.model,
            max_tokens = self.tokens,
            temperature=self.temp,
            system=self.system + ' ' + context, # additional context
            tools=self.tools,
            messages= conversations[id].history[conversations[id].i:]
        )



# specialist
# takes conversation id and json object  in form {"ticker": "META", "period": "5d"}
def specialize(id:int, specializer, static:bool = False):
    data = yf.download(specializer['ticker'],
                       period=specializer['period'], 
                       interval="1h")
    if data is None:
        return ''


    text_block = ''

    if(static):
        text_block = 'The stock went up'
    else:

    # POST - PROCESSOR
    # iterrates over rows , formats them nicely for the model to understand.
        data_str = 'The data is as follows: '
        for idx, row in data.iterrows(): 
            time = idx.strftime("%b %d %Y %I:%M %p") 
            data_str += (
                f"For {time}: the Open is ${float(row['Open'].item()):.2f}, "
                f"High is ${float(row['High'].item()):.2f}, $Low is {float(row['Low'].item()):.2f}, "
                f"Close is ${float(row['Close'].item()):.2f}, $and Volume is {int(row['Volume'].item())}. "
            )

        response = specialist.respond(id,context = data_str)
        text_block = next((b.text for b in response.content if b.type == "text"), '')


    # if data is None: # base case
    #     return ''

    return text_block

class msgItem(BaseModel): # api request base model
    message:str # message 
    is_static: Optional[bool] = None # static testing
    tools_static: Optional[list] = None # static
@app.post('/conversations/{id}/messages') # send user message, return agent resp
def send_message(id: int, item:msgItem):
    if(item.message == ''):
        raise HTTPException(status_code=400,detail="Can't input an empty message.")

    if (id not in conversations): # not found
        raise HTTPException(status_code=404,detail="Conversation id not found.")
    

    #print(intake.system)
    #print(json.dumps(intake.tools, indent=4))


    conversations[id].push_history(item.message) # push message to the history stack

    response = None
    content = None
    tool_blocks = []


    if(item.is_static): # for static testing
        if(item.tools_static):
            tool_blocks = item.tools_static
    else:
        response =  intake.respond(id) # get response
        content = response.content
        tool_blocks = [b.name for b in content if b.type == "tool_use"] # gets the tool blocks


    conversations[id].tokens[intake.key] +=1 # increments key of intake

    if 'collectInterrupt' in tool_blocks: # if an interrupt , pop history except most recent and rerun the response
        conversations[id].pop_history(1) # pop history

        if not item.is_static:
            response = intake.respond(id) # calls token again
            content = response.content
            tool_blocks = [b.name for b in content if b.type == "tool_use"] # gets the tool blocks

        conversations[id].tokens[intake.key] +=1 # increments key of intake

        
    text_block = None
    specializer = None
    
    if item.is_static:
        text_block = 'Static test'

        if(item.tools_static and 'callSpecialist' in item.tools_static):
            specializer = '{"ticker": "META", "period": "5d"}'
    else:
        text_block = next((b.text for b in content if b.type == "text"), '')
        specializer = next((b for b in content if b.type == "tool_use" and b.name == "callSpecialist"), None)


    if specializer: # if a specialist is requird
        # PRE PROCESSOR (specified in config.json)
        # specialist has args for yfinance

        if(item.is_static):
            text_block = specializer
        else:
            text_block = specializer.input['returnVal']
        
        
        text_block = specialize(id, json.loads(text_block), item.is_static) # specializes, draws the data
        if(text_block == ''): # yfinance is down
            raise HTTPException(status_code=500,detail="Internal server error.")
        
        conversations[id].history_handled.append(specialist.key) # appends the bot id (to be retrieved)
        conversations[id].tokens[specialist.key] +=1 # increments key of specialist

    else: # if specialist not required, still at intake
        conversations[id].history_handled.append(intake.key) # appends the bot id (to be retrieved)

    conversations[id].push_history(text_block, user=False) # pushes the text block response

    #print(response.content)

    
    
    return {"message":text_block}
    #history = conversations[id].pop_history() # pops the history from stack

            
    #conversations[id].history
            
            

@app.post('/conversations') # start new conv, return conv id
def new_conv():
    conv_new = conv() 
    return {'id': conv_new.id} # returns conv's id, id and its conv is now in hash


@app.get("/conversations/{id}") # conv history
def conv_history(id:int):

    if (id not in conversations): # not found
        raise HTTPException(status_code=404,detail="Conversation id not found.")
            
    state =  'collecting data' # gets the state of most recent conversation
            
    # check most recent element, if it's intaking, return collecting data

    if(len(conversations[id].history_handled) == 0 or conversations[id].history_handled[-1] == bots_key['specialist']):
        state = 'waiting on new conversation'

    if(len(conversations[id].history) == 0):
        return {
            'state':state,
            'history':{}
        }
    history = []
    for i in range(0,len(conversations[id].history),2):
        history_curr = {'message':conversations[id].history[i]['content'], # every even entry is a user message
                'handledBy':key_bots[conversations[id].history_handled[i//2]], # uses the handled index and retrieves the bot responsible for handling it
                'response':conversations[id].history[i+1]['content']
        }
        history.append(history_curr)

    return {'state': state, # state, string
        'history':history # conv history, list
        }


@app.get("/conversations/{id}/usage") # token usage 
def get_usage(id:int):
    if (id not in conversations): # not found
        raise HTTPException(status_code=404,detail="Conversation id not found.")
            
    return {key_bots[key]:value for key,value in conversations[id].tokens.items()} # converts ids to key names



if __name__ == "__main__":
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)

    i = 0
    for bot in config: # stores the keys 
        if bot == 'shared': # skip shared container
            continue
        bots_key[bot] = i
        key_bots[i] = bot
        i+=1

    intake = agent('intake')
    specialist = agent('specialist')
    
    
    
    if(os.environ.get("ANTHROPIC_API_KEY") is None): # if no key is psecified, return error
        raise Exception('ANTHROPIC_API_KEY not found')
    uvicorn.run(app, host="0.0.0.0", port=8080) # run server on localhost port 8080