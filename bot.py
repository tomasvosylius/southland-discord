# bot.py 
# http://github.com/tomasvosylius/discord-bot
# using discord.py

# -- coding: utf-8 --

import discord
import hashlib
import functionslib as func
from datetime import datetime

admin_channel_id = 705912665444450324
token_file = "token.txt"
server_name = "Southland.lt"
samp_server_ip = "samp.southland.lt:7777"
messages = {
    # message used for DM when new user joins
    "verification_message" : 
        f"Sveikiname prisijungus prie {server_name}! :partying_face:\n"
        f"Jei negali rašyti žinučių Discord kanaluose, privalai patvirtinti savo __telefono numerį__.\n"
        f"Norėdamas patvirtinti savo UCP vartotoją, užsiregistruok serveryje `{samp_server_ip}`\n"
        f"Apie vartotojo patvirtinimą pasiskaityk **#žaidėjo-patvirtinimas**\n"
        f"Jei norėsi atstatyti slaptažodį, naudok !password. Instrukcijas gausi privačiai.",
    "welcome_global" : 
        "Labas, __{0}__! :wave: :tada:\nSveikiname prisijungus prie {1} serverio!"
}

if __name__ == "__main__":
    print("Starting bot.py!")

    token = func.read_token()
    print("Token was read succesfully!")

    client = discord.Client()
    print("Running the client now...")

    # @client.event 
    # async def on_ready():
    #     return

    @client.event
    async def on_member_join(member):
        print(f"{str(member)} just joined the server.")

        # message the user
        dm = await member.create_dm()
        if dm != None:
            await dm.send(messages['verification_message'])


    @client.event
    async def on_connect():
        print("Connected")

    @client.event 
    async def on_message(message):
        """
            Komandos
        """
        if message.author == client.user:
            return # ignore the bot itself

        if message.content.startswith("!ip"):
            await message.channel.send(f"Serverio IP: {samp_server_ip}")

        if message.content.startswith("!myid"):
            await message.channel.send(f"Tavo Discord ID yra {message.author.id}")

        if message.content.startswith("!checkuser"):
            roles = message.author.roles
            admin = False
            for role in roles:
                if role.name == "Management":
                    admin = True
                    break
                    
            if admin:
                if len(message.mentions) == 1 and message.mentions is not None:
                    check_user = message.mentions[0].id
                    if check_user is None:
                        await message.channel.send("Neteisingai nurodytas vartotojas")
                    else:
                        await show_user_data(message.channel, message.author, check_user)
                else:
                    await message.channel.send("Nenurodytas vartotojas")

            else:
                await message.channel.send(f"<@{message.author.id}>, nesi administratorius :x:")


        if message.content.startswith("!verify"):
            args = message.content.split()
            if len(args) != 2:
                await message.channel.send(f"<@{member.id}>, neteisingai nurodei vartotojo vardą :x:")
            else:
                await verify_member(message.channel, message.author, args)
        
        if message.content.startswith("!password"):
            await change_password(message.channel, message.author)
                
    """
        Funkcijos
    """
    async def greet_member(channel, member):
        await channel.send(messages["welcome_global"].format(member.display_name, server_name))

    async def show_user_data(channel, member, check_user):

        db = func.mysql_connect()
        cur = db.cursor()

        sql = f"SELECT `Name`,`id`,`RegisterIp`,`RegisterDate` FROM `users_data` WHERE `DiscordVerified`='2' AND `DiscordUser`='{check_user}'"
        cur.execute(sql)
        row = cur.fetchone()
        if row is None:
            await channel.send(f"Discord narys <@{check_user}> nėra surišęs savo žaidimo vartotojo.")

        else:
            user_id = row[1]
            lpad =  """Discord narys <@{0}> yra patvirtinęs vartotoją **{1}** (ID: {2})```Registracijos IP: {3}\nRegistracijos data: {4}```""".format(
                check_user,
                row[0],
                user_id,
                # func.hide_ip(row[2]),
                row[2],
                row[3]
            )

            await show_game_accounts(lpad, channel, member, user_id)

        cur.close()
        db.close()

    async def show_game_accounts(lpad, channel, admin, user_id):
    
        db = func.mysql_connect()
        cur = db.cursor()

        sql = f"SELECT `Name`,`gpci` FROM `players_data` WHERE `UserId`='{user_id}'"
        cur.execute(sql)
        rows = cur.fetchall()
        if rows is None:
            await channel.send(f"Žaidėjas veikėjų neturi.")

        else:
            string = lpad
            string += "Veikėjai:```"
            
            if rows is None:
                string += "Nėra"

            else:
                for row in rows:
                    string += f"{row[0]}, veikėjo GPCI: {row[1]}\n\n"

            string += "```"
            if len(string) > 0:
                
                await channel.send(f"<@{admin.id}>, vartotojo duomenys ir veikėjai išsiųsti į <#{admin_channel_id}> kanalą.")
                
                await client.wait_until_ready()
                admin_channel = client.get_channel(admin_channel_id)
                await admin_channel.send(string)

        cur.close()    
        db.close()


    async def change_password(channel, member):
        """
            Psw keitimas    
        """

        db = func.mysql_connect()
        cur = db.cursor()

        sql = f"SELECT `DiscordCode`,`id` FROM `users_data` WHERE `DiscordVerified` >= '2' AND `DiscordUser` = '{member.id}'"
        cur.execute(sql)
        row = cur.fetchone()
        if row is not None:
            code = row[0]
            user_id = row[1]
            cur.execute(f"UPDATE `users_data` SET `NeedsPswChange`='1' WHERE `id`='{user_id}'")
            db.commit()

            await channel.send(f"<@{member.id}>, slaptažodžio keitimo instrukcijos išsiųstos PM!")
            dm = await member.create_dm()
            await dm.send(f"Prisijunk į žaidimą ir įvesk savo kodą: `{code}`. Tuomet matysi slaptažodžio keitimą. Sėkmės :wave:")

        else:
            await channel.send(f"<@{member.id}>, tu neturi žaidėjo vartotojo!")

        db.close()
        cur.close()


    async def verify_member(channel, member, args):
        """
            Userio patvirtinimas    
        """

        db = func.mysql_connect()
        cur = db.cursor()

        args[1] = args[1].strip()

        sql = f"SELECT `Name` FROM `users_data` WHERE `DiscordVerified` >= '2' AND `DiscordUser` = '{member.id}'"
        cur.execute(sql)
        row = cur.fetchone()
        if row is not None:
            await channel.send(f"<@{member.id}>, tavo Discord vartotojas jau surištas su žaidimo vartotoju `{row[0]}`. Šiame projekte gali turėti tik vieną žaidimo vartotoją ant to pačio Discord vartotojo :x:")

        else:
            name = args[1].replace('%', '')
            name = name.replace(';', '')
            name = name.replace('-', '')
            name = name.replace('\'', '')
            if len(name) > 0:

                sql = f"SELECT `id`,`DiscordVerified`,`DiscordCode` FROM `users_data` WHERE `Name`='{name}'"
                cur.execute(sql)
                row = cur.fetchone()

                if row is None:
                    await channel.send(f"<@{member.id}>, vartotojas `{name}` serveryje **neegzistuoja** :x:")
                else:
                    user_id = row[0]
                    verified = row[1]
                    code = row[2]

                    if verified == 2:
                        await channel.send(f"<@{member.id}>, vartotojas `{name}` jau yra **patvirtintas** :x:")
                    else:

                        if len(code) <= 0 or verified == 0:
                            now = datetime.now()
                            dt_string = "SOUTHLAND.LT "
                            dt_string += now.strftime("%d/%m/%Y %H:%M:%S")
                            dt_string += " " + str(user_id)
                            code = ""
                            code = hashlib.md5(dt_string.encode()).hexdigest()
                            code = code[0:9]
                            cur.execute(f"UPDATE `users_data` SET `DiscordVerified`='1',`DiscordCode`='{code}',`DiscordUser`='{member.id}' WHERE `id`='{user_id}'")
                            db.commit()

                        await channel.send(f"<@{member.id}>, patvirtinimo kodas išsiųstas į PM. Įveskite jį žaidime. :mailbox_with_mail:")
                        await send_verification_code(member, code)

        db.close()
        cur.close()

    async def send_verification_code(member, code):
        dm = await member.create_dm()
        await dm.send(f"Tavo patvirtinimo kodas yra: `{code}`. Įvesk jį žaidime, sėkmės :wave:")

    client.run(token)
