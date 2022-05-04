FROM python:3.7
RUN apt-get update
RUN apt-get install -y libgdal-dev


COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

EXPOSE 5000
CMD [ "python3", "app.py"]