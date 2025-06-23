FROM python:3.10-slim

COPY requirements.txt /usr/src/app/requirements.txt
WORKDIR /usr/src/app
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /usr/src/app

CMD ["python", "app.py"]




