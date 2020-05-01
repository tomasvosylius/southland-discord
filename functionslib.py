import mysql.connector

def hide_ip(ip):
    if(len(ip)) <= 3:
        return ip

    last_dot = ip.rfind(".")
    returnal = ip[0:(last_dot+1)]
    returnal += "*"*(len(ip) - last_dot - 1)

    return returnal

def mysql_connect():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="southland"
        )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        print("Successfully connected to MySQL")
        return db

    return None


def read_token():
    #  Function reads token from token.txt file in current directory
    with open("token.txt") as file:
        lines = file.readlines()
        return lines[0].strip()

def get_channel_by_name(client, name):
    # Function returns channel if found by given name 
    for channel in client.get_all_channels():
        if name in channel.name:
            print(f"\t{name} was found, returning")
            return channel
    return None