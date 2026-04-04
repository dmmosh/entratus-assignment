import fastapi # api
import uvicorn # server
import os # env
import random # id generation
import json # json from config file
from pydantic import BaseModel # base model for args

import yfinance

from anthropic import Anthropic
from fastapi import FastAPI, HTTPException

app = FastAPI()
conversations = {}
config = None

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
         if('return' in tool):
             tool_curr["input_schema"] = {
                 'type':'object',
                 'properties':{
                     'returnVal':tool['return']
                 },
                 'required':['returnVal']
             }
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
        
        self.tokens = {'intake':0, 'specialist':0} # token counts of agents
        
        self.history = [] # conv logs 
        # each log will consist of who handled it
        # ex {'role':'user','content':'hello'}
        # ex {'role':'assistant','content':'hii'}
        
        self.i = 0 # the index of the bottom of the queue (start of current gathering period)
        # when the conversation is handled by specialist, self.i is moved to len(self.logs) , or the index of the new conversation
    
    def push_history(self,message:str):
        self.history.append({
            'role':'user',
            'content':message
        })

    def pop_history(self): # pops the most recent history in a way which claude api likes
       out = []
       
       self.i = len(self.history) # "pops" from the stack , sets i to new value
       return out # pops history in format the user will like
        
class agent: # calls agent class
    def __init__(self, name):
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
    


            

@app.post('/conversations') # start new conv, return conv id
def new_conv():
    conv_new = conv() 
    return {'id': conv_new.id} # returns conv's id, id and its conv is now in hash


class msgItem(BaseModel):
    message:str


@app.post('/conversations/{id}/messages') # send user message, return agent resp
def send_message(id: int, item:msgItem):
    if(item.message == ''):
        raise HTTPException(status_code=400,detail="Can't input an empty message.")

    if (id not in conversations): # not found
        raise HTTPException(status_code=404,detail="Conversation id not found.")
    
    
    return {"message":item.message}
    #history = conversations[id].pop_history() # pops the history from stack

            
    #conversations[id].history
            
            

@app.get("/conversations/{id}") # conv history
def conv_history(id:int):
    if (id not in conversations): # not found
        raise HTTPException(status_code=404,detail="Conversation id not found.")
            
    state =  'receiving new prompt' # gets the state of most recent conversation
            
    # check most recent element, if it's intaking, return collecting data

    if(len(conversations[id].history)>0 and conversations[id].history[-1]['role'] == 'intake'):
        state = 'collecting data'
            
    history = []
    for i in range(0,len(conversations[id].history),2):
        history_curr = {'message':conversations[id].history[i]['content'], # every even entry is a user message
                'handledBy':
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
            
    return conversations[id].tokens # return the token usage (already a dict)



if __name__ == "__main__":
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)

    i = 0
    for bot in config: # stores the keys 
        if bot == 'shared':
            continue
        bots_key[bot] = i
        key_bots[i] = bot

    intake = agent('intake')
    
    
    if(os.environ.get("ANTHROPIC_API_KEY") is None): # if no key is psecified, return error
        raise Exception('ANTHROPIC_API_KEY not found')
    uvicorn.run(app, host="0.0.0.0", port=8080) # run server on localhost port 8080