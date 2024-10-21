import os
import discord
from google.auth.metrics import token_request_access_token_mds
import requests
import json
import datetime
import nest_asyncio
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

#Settingszs
command_prefix = "$"
free_cards = ["Plains", "Island", "Swamp", "Mountain", "Forest"]
nest_asyncio.apply()

#Connect to Discord
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


#Connect to Google Sheets
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
SAMPLE_SPREADSHEET_ID = ""; #Sheet ID goes here
SAMPLE_RANGE_NAME = "Sheet1!D5:G"
creds = None
if os.path.exists("token.json"):
  creds = Credentials.from_authorized_user_file("token.json", SCOPES)
if not creds or not creds.valid:
  if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
  else:
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)
  with open("token.json", "w") as token:
    token.write(creds.to_json())


# Functions
def send_to_sheet(data, sheet_name, cell_range=""):
  try:
    service = build("sheets", "v4", credentials=creds)
    # Call the Sheets API
    sheet = service.spreadsheets()
    if cell_range != "":
      result = sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=sheet_name+"!"+cell_range, valueInputOption="RAW", body={"values": data}).execute()
      
    else:
      result = (sheet.values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=sheet_name, valueInputOption="RAW", body={"values": data}).execute())
      
    values = result.get("values", [])
    if not values:
      print("No data found.")
      return

    for row in values:
      print(row[0])
    return result
  except HttpError as err:
    print(err)
    return err
  except:
    print("Error")

def read_from_sheet(sheet_name, cell_range=""):
    try:
      service = build("sheets", "v4", credentials=creds)
      # Call the Sheets API
      sheet = service.spreadsheets()
      result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=sheet_name+"!"+cell_range).execute()

      values = result.get("values", [])
      if not values:
        print("No data found.")
        return

      for row in values: 
        #print(row)
        return values
    except HttpError as err:
      print(err)

def clear_sheet_range(sheet_name, cell_range=""):
  try:
    service = build("sheets", "v4", credentials=creds)
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().clear(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=sheet_name+"!"+cell_range).execute()
  
    values = result.get("values", [])
    if not values:
      print("Range cleared.")
      return "CLEAR"
  except HttpError as err:
    print(err)
    return "ERROR"
    
def price_decklist(decklist, print_full_list=False):
  #Prices decklist in it's entirety and returns the total. If print_full_list == True the whole list and individual prices will be returned.
  printout = ""
  total = 0.00

  for cardnames in decklist:
    if cardnames == "" or cardnames == "\n" or cardnames.lower() == "sideboard:" or cardnames.lower() == "sideboard":
      continue
    quantity = cardnames.split(" ", 1)[0].lower().replace("x", "")
   
    cardname_nospace = cardnames.split(" (", 1)[0]
    print(cardnames)
    cardname = cardname_nospace.split(" ", 1)[1]
    cardname = cardname.replace(" ", "+")

    api_call = "https://api.scryfall.com/cards/named?fuzzy=" + cardname
    response = requests.get(api_call).content
    parsed = json.loads(response)
    printings_uri = parsed.get("prints_search_uri")
    if str(requests.get(api_call)) == "<Response [200]>":
      printings_data = json.loads(requests.get(printings_uri).content).get("data")
    low_cardprice = 1000
    if str(requests.get(api_call)) == "<Response [200]>":
      for printings in printings_data:
        prices = printings.get("prices")
        cardprice = 1000
        if prices["usd"] != None:
           cardprice = float(prices["usd"])
        if prices["usd_foil"] != None:
          if float(prices["usd_foil"]) < cardprice:
             cardprice = float(prices["usd_foil"])
        if prices["usd_etched"] != None:
          if float(prices["usd_etched"]) < cardprice:
             cardprice = float(prices["usd_etched"])
        if cardprice < low_cardprice:
          low_cardprice = cardprice
          cheap_print = printings.get("set")
    for cards in free_cards:
      if cardname == cards:
        low_cardprice = 0.00
        
    if low_cardprice != 1000:
      total += (low_cardprice*float(quantity))
    if print_full_list == True:  
      if low_cardprice == 1000:
        printout = printout + "No price found for '" + cardname.replace("+", " ") + "'\n"
      else:
        printout = printout + "$" + str(low_cardprice) + " - " + str(cardname_nospace) + " " + cheap_print.upper() + "\n"
    if cardnames == decklist[-1]:
      r = requests.put("https://docs.google.com/spreadsheets/d/17dSaSDAPrPdVJNH3__n1uIhd_dMex9vyf1eJqDoeu6I/edit#gid=2:2", data={"id":1, "total":total, "name":"Ashhuston"})
      print(r)
      if print_full_list == True:  
       return printout + "Total: $" + str(round(total, 2))
      else:
        return round(total, 2)

def get_moxfield_info(moxfieldUrl):
  # Returns an array of information from the link. In the order of DECKNAME(string), PRICE(tcglow)(string), DECKLIST(string)
    while(True):
        output = []
        driver = webdriver.Chrome()
        driver.get(moxfieldUrl)
        waitSeconds = 10
        driver.implicitly_wait(waitSeconds)
        buyBtn = driver.find_element(By.LINK_TEXT, 'Buy')
        buyBtn.send_keys(Keys.RETURN)
        tcgRadio = driver.find_element(By.ID, 'affiliate-tcgplayer')
        tcgRadio.click()
        modalFooter = driver.find_element(By.CLASS_NAME, 'modal-footer')
        spans = modalFooter.find_elements(By.TAG_NAME, 'span')
        price = ""
        for each in spans:
            if each.text.count('$')>0:
                price = each.text
        closeBtn = driver.find_element(By.CLASS_NAME, "btn-close")
        closeBtn.send_keys(Keys.RETURN)
        elem = driver.find_element(By.ID, "subheader-more")
        elem.send_keys(Keys.RETURN)
        assert "No results found." not in driver.page_source
        exportBtn = driver.find_element(By.LINK_TEXT, 'Export')
        exportBtn.send_keys(Keys.RETURN)
        decklistTextBox = driver.find_element(By.NAME, "full")

        textDecklist = ''
    
        for lines in decklistTextBox.text.splitlines():
            textDecklist += (lines.split('(')[0] + '\n')
        
        deckName = driver.find_element(By.CLASS_NAME, 'deckheader-name')
        output.append(deckName.text)
        output.append(price)
        output.append(textDecklist)
        driver.close()
        if price != "":
            return output


# Confirms connection.  
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
  
#Manages all server commands.
@client.event
async def on_message(message):
  #Ignores bots own messages
    if message.author == client.user:
        return
  # convert message to just command.
    if message.content.startswith(command_prefix):
      command_call = message.content.split(" ", 1)[0].lower()
      print(command_call + " has been called by " + str(message.author))
    else:
      return
#------------------------------ COMMANDS ------------------------------#
  #---------- Help ----------#
    if command_call.startswith(command_prefix + 'help'):   
      help_text = "Commands with multiple parameters are separated by a comma.\nSome commands may take a moment to respond. This is normal.\n# $price\n$price DECKLIST\nLists prices, cheapest printings, and total price of a decklist. Must receive decklist in the form of X cardname with one card per line, no set/collectors number information. Moxfield export to MTGO works as is.\n\n# $addevent\n$addevent NAME, DATE, TIME, LOCATION, REL\nMods only.\nAdds an event to the events list. Does not make it available for registration. Parameters are comma separated and can include spaces. \nTo make an event open for registration, simply add a sheet. You should not add an event before adding a registration sheet, else it’ll show up when users call $listevents even though they can’t access it.\n\n# $register\n$register PLAYER_NAME, EVENT, MOXFIELD_LINK, DECKLIST\nAdds the user to the chosen event’s registration page. If they are already registered (unique by discord id) it will update their information.\n\n# $listevents\nLists out all events currently added to the events sheet.\n\n# $regdetails\n$regdetails EVENT\nLists the details for the calling user (by discord id) for the given event.\n\n# $dropevent\n$dropevent EVENT\nDrops the calling player (unique by discord id) from the given event.\n\n# $playercount\n$playercount EVENT\nLists the number of registered players for the given event."
      if  len(message.content.split(" ", 1)) == 2 and message.content.split(" ", 1)[1].lower() == "in_server":
        await message.channel.send(help_text)
      else:
        try:
          dm = await message.author.create_dm()
          await dm.send(help_text)
        except:
          await message.channel.send(f"User {message.author.mention} has non-friend DMs disabled. To view the help menu, please enable DMs or call '$help in_server'.")
      
  #---------- Price ----------#
    if command_call.startswith(command_prefix + 'price'):
      await message.channel.send("Processing...")
      command = message.content.split(" ", 1)
      decklist = command[1].splitlines()
      if not isinstance(message.channel, discord.channel.DMChannel):
          await message.delete()
      try:
          await message.channel.send(f"{message.author.mention}\n" + str(price_decklist(decklist, True)))
      except:
          dm = await message.author.create_dm()
          await dm.send(f"{message.author.mention}\n" + str(price_decklist(decklist, True)))
          
  #---------- AddEvent ----------#
    if command_call.startswith(command_prefix + 'addevent'):
      def add_event(message, name="", date="", time="", location="", REL=""):
        if name == "" or date == "" or time == "" or location == "" or REL == "" :
            message.channel.send("ERROR: Missing parameters. Command should look like '$add_event name date time location REL active_registration(True/False')")
        else:
          print(name)
          data = [[name, date, time, location, REL]]
          send_to_sheet(data, "Events", "")

      
      role = discord.utils.find(lambda r: r.name == 'Mod', message.guild.roles)
      if role in message.author.roles:
        # $addevent name, date, time, location, REL, active_registration
        params = message.content.split(" ", 1)[1]
        command = params.split(", ", 4)
        if len(command) >= 5:
          name = str(command[0])
          date = str(command[1])
          time = str(command[2])
          location = str(command[3])
          REL = str(command[4])
          if not isinstance(message.channel, discord.channel.DMChannel):
            await message.delete()
          await message.channel.send("Event added!")
          add_event(message, name, date, time, location, REL)
        else:
         await message.channel.send("ERROR: Missing parameters. Command should look like '$addevent name, date, time, location, REL'")
      else:
        if not isinstance(message.channel, discord.channel.DMChannel):
          await message.delete()
        await message.channel.send(f"{message.author.mention} You do not have permission to use the command '$addevent'.")


        
  #---------- Register ----------#
    if command_call.startswith(command_prefix + 'register'):
     
      # $register player_name, event, moxfield_link, decklist
      channel = message.channel
      params = message.content.split(" ", 1)[1]
      if not isinstance(message.channel, discord.channel.DMChannel):
          await message.delete()
      await channel.send("Processing...")
      command = params.split(", ", 3)
      if len(command) >= 4:
        player_name = str(command[0])
        event = str(command[1]).lower().replace("’", "").replace("'", "").strip()
        moxfield_link = str(command[2])
        decklist = get_moxfield_info(moxfield_link)[2]
        price = float(get_moxfield_info(moxfield_link)[1].strip('$'))
        varified = False
        if price <= 30:
          varified = True

        # Check if player is already registered
        players_arr = read_from_sheet(event, "B2:B500")
        list = ""
        cnt=2
        player_is_registered = False
        if players_arr != None:
          for players in players_arr:
            if str(players[0]) == str(message.author):
              player_is_registered = True
              break
            else:
                player_is_registered = False
                cnt+=1
        else: 
            print("No players detected!")
        if player_is_registered == True:
          
            code = str(send_to_sheet([[player_name, str(message.author), str(datetime.datetime.now()), decklist, moxfield_link, varified, price]], event, "A"+str(cnt)+":Z"))
            if code.startswith("<HttpError 400"):
              await channel.send("ERROR: Something went wrong. Make sure event name is exact. Try $listevents to see all events.")
            else:
              await channel.send(f"{message.author.mention}" + " your registration details for " + event + " has been updated!")
          
        else:
          code = str(send_to_sheet([[player_name, str(message.author), str(datetime.datetime.now()), decklist, moxfield_link, varified, price]], event))
          if code.startswith("<HttpError 400"):
            await channel.send("ERROR: Something went wrong. Make sure event name is exact. Try $listevents to see all events.")
          else:
           await channel.send(f"{message.author.mention}" + " is successfully registered for " + event + "!")

      
      else:
        await channel.send("ERROR: Missing parameters. Command should look like '$register player_name, event, moxfield_link, decklist'")
        

  #---------- ListEvents ----------#
    if command_call.startswith(command_prefix + 'listevents'):
      events_arr = read_from_sheet("Events", "A2:A500")
      open_arr = read_from_sheet("Events", "F2:F500")
      list = ""
      cnt = 0
      for events in events_arr:
        try:
            if open_arr[cnt][0] == "TRUE":
                list = list + str(events[0]) + " - Open\n"
            else:
                list = list + str(events[0]) + " - Closed\n"
        except:
            print("Blank event skipped in listing.")
        cnt += 1
      await message.channel.send(f"Events:\n" + list)
      if not isinstance(message.channel, discord.channel.DMChannel):
          await message.delete()


  #---------- RegDetails ----------#
    if command_call.startswith(command_prefix + 'regdetails'):

      channel = message.channel
      if len(message.content.split(" ", 1)) >= 2:
        params = message.content.split(" ", 1)[1].split(", ", 1)
        event = str(params[0]).lower().replace("’", "").strip()
        
        players_arr = read_from_sheet(event, "B2:B500")
        cnt=2
        player_is_registered = False
        if players_arr != None:
          for players in players_arr:
            if players[0] == str(message.author):
              player_is_registered = True
              break
          else:
            player_is_registered = False
            cnt+=1
  
        if player_is_registered == True:
            details = read_from_sheet(event, "A"+str(cnt)+":Z")
            date = details[0][2].split(" ", 1)[0]
            print_str = f"{message.author.mention}" + " your registration details for " + event + " are:\nName: " + details[0][0] + "\nSubmission date: " + date + "\nMoxfield link: " + details[0][4] + "\nPrice: " + details[0][6] + "\nDecklist: \n" + details[0][3]
  
            if str(details).startswith("<HttpError 400"):
                await channel.send("ERROR: Something went wrong. Make sure event name is exact. Try $listevents to see all events.")
            else: 
              if len(params) == 2 and params[1] == "in_server":
                await message.channel.send(print_str)
              else:
                try:
                  dm = await message.author.create_dm()
                  await dm.send(print_str)
                except:
                  await message.channel.send(f"User {message.author.mention} has non-friend DMs disabled. To view the help menu, please enable DMs or call '$regdetails event, in_server'.")
              if not isinstance(message.channel, discord.channel.DMChannel):
                await message.delete()
        else:
          if len(params) == 2 and params[1] == "in_server":
            await message.channel.send(f"{message.author.mention} You are not registered for '" + event + "'.")
          else:
            try:
              dm = await message.author.create_dm()
              await dm.send("You are not registered for '" + event + "'.")
            except:
              await message.channel.send(f"User {message.author.mention} has non-friend DMs disabled. To view the help menu, please enable DMs or call '$regdetails event, in_server'.")
            if not isinstance(message.channel, discord.channel.DMChannel):
                await message.delete()
      else:
         await channel.send("ERROR: Missing parameters. Command should look like '$regdetails event'")
         if not isinstance(message.channel, discord.channel.DMChannel):
          await message.delete()

  
  
  #---------- DropEvent ----------#
    if command_call.startswith(command_prefix + 'dropevent') or command_call.startswith(command_prefix + 'drop'):
      channel = message.channel
      if len(message.content.split(" ", 1)) >= 2:
        params = message.content.split(" ", 1)[1]
        event = str(params).lower().replace("’", "").strip()

        players_arr = read_from_sheet(event, "B2:B500")
        cnt=2
        for players in players_arr:
          if players[0] == str(message.author):
            player_is_registered = True
            break
          else:
            player_is_registered = False
            cnt+=1

        if player_is_registered == True:

            drop = clear_sheet_range(event, "A"+str(cnt)+":Z")
            

            if drop == "ERROR":
                await channel.send("ERROR: Something went wrong. Make sure event name is exact. Try $listevents to see all events. If you are sure the event exists, try contacting a Moderator")
            else:  
                await channel.send(f"{message.author.mention}" + " you have been dropped from '" + event + "'.")  
                if not isinstance(message.channel, discord.channel.DMChannel):
                    await message.delete()
        else:
          await channel.send("You are not registered for this event.")
          if not isinstance(message.channel, discord.channel.DMChannel):
            await message.delete()
      else:
         await channel.send("ERROR: Missing parameters. Command should look like '$regdetails event'")
         if not isinstance(message.channel, discord.channel.DMChannel):
            await message.delete()
        

  #---------- PlayerCount ----------#
    if command_call.startswith(command_prefix + 'playercount'):
      channel = message.channel
      if len(message.content.split(" ", 1)) >= 2:
        params = message.content.split(" ", 1)[1]
        event = str(params).lower().replace("’", "").strip()
  
        players_arr = read_from_sheet(event, "B2:B500")
        cnt=0
        if players_arr != None:
          for players in players_arr:
              cnt+=1
        await channel.send("There are " + str(cnt) + " players registered for '" + event + "'.")
        if not isinstance(message.channel, discord.channel.DMChannel):
          await message.delete()
      else:
         await channel.send("ERROR: Missing parameters. Command should look like '$regdetails event'")
         if not isinstance(message.channel, discord.channel.DMChannel):
          await message.delete()

try:
  token = "" or "" ##Add token here
  if token == "":
    raise Exception("Please fix discord token.")
  client.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        print(
            "The Discord servers denied the connection for making too many requests"
        )
        print(
            "Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests"
        )
    else:
        raise e