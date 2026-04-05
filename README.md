# entratus-assignment

Antratus assignment submission by Dmytro Moshkovskyi.
The example is a stock tracker chatbot who can retrieve stock prices and some basic stock info on them using a two-agent setup.

## Environment variable required: 
- ANTHROPIC_API_KEY

## Building:
`docker build -t entratus-assignment . `

## Running:
If you have ANTHROPIC_API_KEY as your environment variable:

`docker run -e ANTHROPIC_API_KEY -p 8080:8080 entratus-assignment `

If you don't:

`docker run -e ANTHROPIC_API_KEY=<api key> -p 8080:8080 entratus-assignment `

## Testing:
` python test.py  # runs several tests `