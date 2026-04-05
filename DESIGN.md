A
    I would stream using SSE communication, by Claude's built-in client.messages.stream.
    I would keep a buffer, growing it with every iteration of text_stream, until a sentence-ending character is caught by a regex (. , ; ! ? etc). When that happens, send the buffer to TTS and clear the buffer. 
    This would be implemented by a next index counter and a priority queue on the client side, with each chunk having a unique number corresponding to its ordering. The next index counter increments when an element with a matching number on a chunk comes in. If there are chunks with a higher number already waiting in the queue, the new chunk goes down until it reaches its sorted position in the queue or gets popped (delivered). On the latter, the next index counter is incremented, and any sorted chunks in the queue that satisfy the next index counter get popped as well. 


B
    First off, did it answer the question it reasonably could? This will be scored out of 3 points, flat 0 or 3. There are 2 scenarios: conversation was answered correctly or out of bounds of the model was correctly unanswered. This will be evaluated on an LLM because the Specialist could give a wrong/partial answer. The Specialist could also give an answer which was out of bounds of the model. 
    Secondly, did it call the specialist when just enough context has been gathered? Not too little information, where the model makes assumptions (could be in-line with the intended result), but neither too much information, where an answer could've been deduced earlier. This will be scored a value out of 3. “Just enough” is subjective, so LLM-based testing with strict behavioral constraints is required. 
    Finally, is the data correct? This checks if the data is correct. More specifically, it targets the multitude of small calculations that the model can make on the provided stock data. This is done by a LLM + rule-based approach. First, the Specialist's output is analyzed and converted into a predefined layout with the dates of the data selected. The dates are then used to retrieve the same data from yfinance before performing calculations manually before comparing them to the converted layout. It is scored out of 3 points depending on how many of the values are correct. 
Answered in part 1.
    The scoring would be handled by a queue running on another thread. When the Specialist returns the data with a response, the indices corresponding to the beginning and the end of the conversation history, as well as the conversation id, are added to the queue. Once an element at the bottom of the queue is popped, the indices will be used to retrieve its conversation history. 


C
    The configuration schema would need to have fields which allow complex branching into multiple agents without using tools. A tool is essentially an if statement. If an agent could route to 20 other agents, especially if branching is dependent on a simple condition, implementing it with tools will be very tedious. 
    I would delegate a router agent, who is the entry point of the request, to route to the most competent agent. There will be behavioral constraints such that the router routes to only one agent. This will be done using complex branching as described in part 1.
    The current design assumes that every agent is assigned to every conversation. There are no restrictions on which agent(s) can be called to the conversation. If an agent routes to another agent that is not intended to be in the conversation, it could derail the conversation. As a result, a net is needed to keep the conversation on-topic while cycling between multiple agents. A fix would be to implement a system which dynamically changes the available agents by a periodic router agent, which updates the delegated agents. 


D 
    In config.json, I would override the shared's avgChar (Claude token is about ~4 chars, max allowed token usage being avgChar//4) by setting a custom avgChar in the agent's config section. 
    I would take the sum of the tokens used for every agent call and multiply it by the per-token price of the model that is assigned to the agent. 
    I would find all of the conversation ids which correspond to the user and repeat step 2. From these, a user can find metrics such as the price of every conversation, the total billing cost for a given period, etc. 
