import json
import os
import typing
try:
    import k_amino.lib
except ModuleNotFoundError:
    os.system("pip install --upgrade k-amino.py")
    raise RuntimeError("reload is required after install k-amino.py") from None

################
savePath = "acc.json"
#############


def clear() -> None:
    os.system('cls' if os.name=='nt' else 'clear')


info = (
    "~ e: Exit\n"
    "~ Press Enter to continue\n"
)


infoError = (
    "~ Invalid account, do you want to save it? [Y/N]: "
)


clear()


print(
    "save accounts in {}\n".upper().format(repr(savePath)) +
    "necessary data:".capitalize(),
    "email,".capitalize(), "password".capitalize()
)


def show_accounts() -> None:
    print("\n~ Accounts: %d" % len(accounts))

accounts: typing.List[typing.Dict[str, str]] = []

if os.path.exists(savePath):
    with open(savePath, 'r') as file:
        accounts.extend(json.load(file))

while True:
    show_accounts()
    amino = k_amino.Client()
    email = input("~ Email: ")
    password = input("~ Password: ")
    device = amino.deviceId
    try:
        amino.login(email, password)
    except k_amino.lib.APIError as api:
        print("~ error:", "({})".format(type(api).__name__), api.message)
        if input(infoError).lower().strip() == "n":
            continue
    except k_amino.lib.AminoBaseException as exc:
        print("~ error:", repr(exc))
        if input(infoError).lower().strip() == "n":
            continue
    accounts.append(dict(
        email=email,
        password=password,
        device=device
    ))
    with open(savePath, 'w') as f:
        json.dump(accounts, f, indent=4)
        print('~ %r saved!' % email)
