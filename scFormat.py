import discord, csv

# Loads csv of filename into a dict and returns it
def csv_to_dict(filename):
    reader = csv.reader(open(filename, 'r'))
    dict = {}
    for k, v in reader:
        dict[k] = v
    return dict

building_names = csv_to_dict("./scBuildingNames.csv")
building_text = csv_to_dict("./scBuildingText.csv")

# Translate number n and number p to a bar graph representing the percentage that n is of p; numbers larger than 100% default to a full bar
def barify(n, p):

    if p == -1:
        return  ''.join(["░" for remaining in range(10)]), -1

    round_percentage = int((n / p) * 100)
    ratio = round_percentage // 10
    if ratio > 10:
        return "██████████"
    return ''.join(["█" for multiple in range(ratio)] + ["░" for remaining in range(10 - ratio)]), round_percentage

def format_join(username, settlementname):
    embed = discord.Embed(title = "WELCOME TO THE GAME [" + username + "]",  description = "Welcome to the SILENT COAST, a post-apocalyptic city management idle game!")
    embed.add_field(name = "FOUNDING YOUR SETTLEMENT [" + settlementname + "]", value = "To start, you must choose a starting tile for your settlement, be it a coastal trading town or a fortress in the hinterlands. Your starting tile determines your per cycle yields (you get one of each in addition), but it also determines what tiles you're likely to get as you expand, as well as what events you might encounter.", inline = False)
    embed.add_field(name = "-", value = "1. COAST     [FUNDS: 3 INDUSTRY: 1 FOOD: 4 SIZE: 4 DEF: 0]: A higher chance of getting COAST, MARSH, and HILLS tiles. Additional marine-themed events.", inline = False)
    embed.add_field(name = "-", value = "2. PLAINS    [FUNDS: 2 INDUSTRY: 1 FOOD: 5 SIZE: 6 DEF: -5]: A higher chance of getting PLAINS and FOREST tiles. Higher chance of prosperity events, but also higher chance of raids.", inline = False)
    embed.add_field(name = "-", value = "3. HILLS     [FUNDS: 1 INDUSTRY: 5 FOOD: 1 SIZE: 3 DEF: 0]: A higher chance of getting HILLS, COAST, and MOUNTAINS tiles. Additional rugged, frontiersy events.", inline = False)
    embed.add_field(name = "-", value = "4. MOUNTAINS [FUNDS: 5 INDUSTRY: 4 FOOD: 0 SIZE: 1 DEF: 10]: A higher chance of getting MOUNTAINS and HILLS tiles. Events of all types are scarce.", inline = False)
    embed.add_field(name = "-", value = "5. MARSH     [FUNDS: 1 INDUSTRY: 0 FOOD: 7 SIZE: 2 DEF: 15]: A higher chance of getting MARSH, COAST, and FOREST tiles. Low raid chance, but also low prosperity events.", inline = False)
    embed.add_field(name = "-", value = "6. FOREST    [FUNDS: 2 INDUSTRY: 3 FOOD: 2 SIZE: 3 DEF: 10]: A higher chance of getting FOREST, PLAINS, and HILLS tiles. Additional forest and wildlife events.", inline = False)
    embed.add_field(name = "SELECT BELOW", value = "--------------", inline = False)
    return embed

def building_stats(building):

    building = [str(item) for item in building]

    name = "BUILD STRING: `" + building[1] + "`"
    fundcost = "\nFUND COST: " + building[2]
    artifcost = " ARTIFACT COST: " + building[3]
    iccost = "\nCONSTRUCTION COST: " + building[5]
    artifrate = " ARTIFACT RATE: " + building[7]
    fifp = "\n FIFP: [" + ' '.join([building[6], building[8], building[9], building[10]]) + "]"
    defense = "\n DEFENSE: " + building[12]
    attack = " ATTACK: " + building[13]
    slots = "\n SLOTS USED: " + building[11]
    weird = " WEIRDNESS: " + building[14]
    
    return name + fundcost + artifcost + iccost + artifrate + fifp + defense + attack + slots + weird

def format_buildinglist(buildings, tier):
    embed = discord.Embed(title = "TIER " + tier + " BUILDINGS")
    for building in buildings:
        embed.add_field(name = building_names[building[1]], value = building_stats(building), inline = True)
    return embed

def format_build(building_name, building):
    embed = discord.Embed(title = building_names[building_name])
    embed.add_field(name = "ABOUT", value = building_text[building_name], inline = False)
    embed.add_field(name = "STATS", value = building_stats(building), inline = False)
    embed.add_field(name = "DO YOU WISH TO CONSTRUCT THIS BUILDING?", value = "(yes/no)", inline = False)
    return embed

def format_status(user_s_row, icbar, popbar, isbuilding, building):
    embed = discord.Embed(title = "The settlement of " + user_s_row[1])
    # format is fundtotal 0, fundrate 1, artifacttotal 2, artifactrate 3, industry 4, food 5, power 6, def 7, attack 8, free slots 9, strange 10
    data = [user_s_row[4], user_s_row[5], user_s_row[6], user_s_row[7], user_s_row[8], user_s_row[9], user_s_row[10], user_s_row[11], user_s_row[12], user_s_row[13] - user_s_row[14], user_s_row[15]]

    if isbuilding:

        embed.add_field(name = "CONSTRUCTION:", value = building_names[building] + "\n" + icbar[0] + "  " + str(icbar[1]) + "%", inline = False)

    else:

        embed.add_field(name = "CONSTRUCTION:", value = "NO CONSTRUCTION", inline = False)

    # RENDER POP BAR HERE
    # THIS SHOULD ALWAYS BE HERE

    embed.add_field(name = "FUNDS STORED:", value = data[0], inline = True)
    embed.add_field(name = "ARTIFACTS STORED:", value = data[2], inline = True)
    embed.add_field(name = "FUNDS PER CYCLE:", value = data[1], inline = True)
    embed.add_field(name = "ARTIF. PER CYCLE:", value = data[3], inline = True)

    embed.add_field(name = "INDUSTRY", value = data[4], inline = True)
    embed.add_field(name = "FOOD", value = data[5], inline = True)

    embed.add_field(name = "SETTLMT. POWER", value = data[6], inline = True)
    embed.add_field(name = "SETTLMT. STRANGNESS", value = data[10], inline = True)

    embed.add_field(name = "DEFENSE", value = data[7], inline = True)
    embed.add_field(name = "ATTACK", value = data[8], inline = True)
    
    embed.add_field(name = "FREE BUILD SLOTS", value = data[9], inline = True)

    return embed