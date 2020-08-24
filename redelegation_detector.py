import websocket
import json
import requests
from requests import Request, Session
import asyncio
import discord
from discord.ext import commands
from discord.utils import get

TOKEN = '' # Replace with your discord token

rep_address = 'nano_1maffswnif9r35yy6btgo7qukpnpzhpndegi7895fobfjffgfr9pjdy9f66w' #Replace with your rep
rep_name = 'maffs rep' # Replace with your rep name
channel_id = 0 # Replace with the ID of the channel you want the bot to broadcase the notification in.

bot = commands.Bot(command_prefix='?') # command_prefix not actually needed but the bot doesn't run without a prefix
bot.remove_command('help')

def convert_raw_to_NANO(raw,decimals):
    NANO = raw/10**30
    if decimals == 0:
        return int(round(NANO))
    else:
        return round(NANO, decimals)

def find_online_weight():
    info = requests.post("http://127.0.0.1:7076", 
                    json = {
                    "action": "confirmation_quorum",
                    }
                ).json()['online_stake_total']
    return int(info)

def find_voting_weight(address):
    info = requests.post("http://127.0.0.1:7076", 
                    json = {
                    "action": "account_weight",
                    "account": address
                    }
                ).json()['weight']
    return int(info)

def find_wallet_balance(address):
    info = requests.post("http://127.0.0.1:7076", 
                    json = {
                    "action": "account_balance",
                    "account": address
                    }
                ).json()['balance']
    return int(info)

def find_voting_weight_percentage(address):
    online_weight = find_online_weight()
    address_weight = find_voting_weight(address)

    return round(address_weight/online_weight*100,2)


async def send_block_to_channel(block):
    ann_channel = bot.get_channel(channel_id)

    account = block["message"]["account"]
    blockhash = block["message"]["hash"]

    msg = f'`{account}` has changed their representative address to {rep_name}!'
    
    embed = embed = discord.Embed(
        color = 4886754,
        title = 'Redelegation Alert',
        description = msg,
    )

    wallet_balance = find_wallet_balance(account)
    NANO_balance = convert_raw_to_NANO(wallet_balance,3)

    embed.add_field(
        name = "Weight Added",
        value = f"{NANO_balance} NANO"
    )

    embed.add_field(
        name = "Link to Block",
        value = f"https://nanocrawler.cc/explorer/block/{blockhash}",
    )

    embed.set_footer(
        text = f"Voting weight is now {convert_raw_to_NANO(find_voting_weight(rep_address),0)} NANO, which is {find_voting_weight_percentage(rep_address)}% of online weight."
    )
    
    await ann_channel.send(embed=embed)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    websocket.enableTrace(True)
    ws = websocket.create_connection("ws://127.0.0.1:7078/")

    ws.send('{"action": "subscribe", "topic": "confirmation"}')

    print("Receiving...")
    while True:
        result = ws.recv()
        block = json.loads(result)
        if block["message"]["block"]["subtype"] == "change" and block["message"]["block"]["representative"] == rep_address:
            await send_block_to_channel(block)
            print(result)

    ws.close()

bot.run(TOKEN)