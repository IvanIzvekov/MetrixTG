# pull the official docker image
FROM python:3.11

# set work directory
WORKDIR /src

# install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .

CMD [ "python", "./main.py"]
