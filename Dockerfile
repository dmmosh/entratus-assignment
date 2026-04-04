# python 3.14
FROM python:3.14-slim 

# get api key
ARG ANTHROPIC_API_KEY_ENV
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY_ENV}

# standard convention
WORKDIR /app 
COPY . /app

# install pip requirements
RUN pip install --no-cache-dir -r requirements.txt

#default port for server
ENV PORT=8000
EXPOSE 8000

#RUN npm install
CMD ["python", "src/main.py"]