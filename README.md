# entratus-assignment

Antratus assignment submission by Dmytro Moshkovskyi.
The example is a stock tracker chatbot who can retrieve stock prices and some basic math operations.

## Environment variable required: 
- OPENAI_API_KEY

## Building:
`docker build -t entratus-assignment . `

## Running:
If you have OPENAI_API_KEY as your environment variable:

`docker run -e OPENAI_API_KEY -p 8080:8080 entratus-assignment `

If you don't:

`docker run -e OPENAI_API_KEY=<api key> -p 8080:8080 entratus-assignment `

## Endpoints:
wip

## Testing:
wip