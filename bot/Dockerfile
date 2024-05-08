FROM python:3.11
# base image vresion 3.11

WORKDIR /bot

COPY . .
# source - destination

RUN pip install -r requirements.txt
# able to do this cuz already copied this file

CMD ["python", "./bot.py"]
# run bot after everything's ready
