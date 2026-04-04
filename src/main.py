import fastapi # api
import uvicorn # server
import os # env
import random # id generation

from anthropic import Anthropic
from fastapi import FastAPI, HTTPException

app = FastAPI()
conversations = {}

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
                # ex {'handledBy':'intake','content':'hello'}
                
                self.i = 0 # the index of the bottom of the queue (start of current gathering period)
                # when the conversation is handled by specialist, self.i is moved to len(self.logs) , or the index of the new conversation
                

                        

@app.post('/conversations') # start new conv, return conv id
def new_conv():
        conv_new = conv() 
        return {'id': conv_new.id} # returns conv's id, id and its conv is now in hash



@app.post('/conversations/{id}/messages') # send user message, return agent resp
def send_message(id: int, message:str):
        if (id not in conversations): # not found
                raise HTTPException(status_code=404,detail="Conversation id not found.")
        
        
        
        #conversations[id].history 
        
        
        

@app.get("/conversations/{id}") # conv history
def conv_history(id:int):
        if (id not in conversations): # not found
                raise HTTPException(status_code=404,detail="Conversation id not found.")
        
        state =  'receiving new prompt' # gets the state of most recent conversation
        
        # check most recent element, if it's intaking, return collecting data
        if(len(conversations[id].history)>0 and conversations[id].history[-1]['handledBy'] == 'intake'):
                state = 'collecting data'
                
        return {'state': state, # state, string
                'history':conversations[id].history # conv history, list
                }



@app.get("/conversations/{id}/usage") # token usage 
def get_usage(id:int):
        if (id not in conversations): # not found
                raise HTTPException(status_code=404,detail="Conversation id not found.")
        
        return conversations[id].tokens # return the token usage (already a dict)



if __name__ == "__main__":

        if(os.environ.get("ANTHROPIC_API_KEY") is None): # if no key is psecified, return error
                raise Exception('ANTHROPIC_API_KEY not found')
        uvicorn.run(app, host="0.0.0.0", port=8080) # run server on localhost port 8080