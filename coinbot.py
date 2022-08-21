email, password = ["email goes here", "password goes here"]
commandPrefix, amountPerTransfer = ["!", 40]
from os import system
from time import sleep, time
from json import load, dump
for x in ["amino", "dick.py"]: system(f"pip uninstall {x}")
try: from amino import Client, SubClient
except ImportError: system("pip install --upgrade amino.py")
client = Client()
client.login(email=email, password=password)

@client.event("on_text_message")
def onCoinCommand(data):
    if data.message.content.startswith(commandPrefix + "coins"):
        messageId = data.json["chatMessage"]["messageId"]
        subclient = SubClient(comId=data.comId, profile=client.profile)
        if data.json["chatMessage"]["author"]["level"] < 5:
            subclient.send_message(chatId=data.message.chatId,
            message="You must be level 5 or above to use this command", replyTo=messageId)
        if client.userId == data.json["chatMessage"]["uid"]: 
            subclient.send_message(chatId=data.message.chatId,
            message="You can't use this command on yourself", replyTo=messageId)
        else:
            coinFunction(subclient=subclient, comId=data.comId, userId=data.json["chatMessage"]["uid"],
            chatId=data.message.chatId, messageId=messageId)

def coinFunction(subclient: SubClient, comId: str, userId: str, chatId: str, messageId: str):
    blogId = subclient.get_user_blogs(userId=userId).blogId[0]
    if blogId is not None:
        if coinUsers(userId=userId):
            subclient.send_coins(blogId=blogId, coins=amountPerTransfer)
            subclient.send_message(chatId=chatId,
            message=f"[ic]Sent {amountPerTransfer} coins to \n[ic]narviiapp://x{comId}/blog/{blogId}", replyTo=messageId)
        else:
            subclient.send_message(chatId=chatId, replyTo=messageId,
            message="You have already claimed your coins for the day, try again tomorrow.")
    else:
        subclient.send_message(chatId=chatId, replyTo=messageId,
        message="No blogs found, please create a blog and try again.")

def coinUsers(userId: str):
    currentTime = time()
    try:
        with open("coinUsers.json", "r") as f:
            userIds = load(f)
    except FileNotFoundError:
        open("coinUsers.json", "w").write("{}")

    if userId in userIds:
        if currentTime - userIds[userId] > 43200:
            userIds[userId] = currentTime
            with open("coinUsers.json", "w") as f:
                dump(userIds, f, indent=4)
            return True
        else: return False
    else:
        userIds[userId] = currentTime
        with open("coinUsers.json", "w") as f:
            dump(userIds, f, indent=4)
        return True

while True:
    sleep(60)
