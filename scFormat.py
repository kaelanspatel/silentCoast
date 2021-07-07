import discord

# Translate number n and number p to a bar graph representing the percentage that n is of p; numbers larger than 100% default to a full bar
def barify(n, p):
    round_percentage = int((n / p) * 100)
    ratio = round_percentage // 10
    if ratio > 10:
        return "██████████"
    return ''.join(["█" for multiple in range(ratio)] + ["░" for remaining in range(10 - ratio)]), round_percentage


def format_join(username, settlementname):
    embed = discord.Embed(title = "WELCOME TO THE GAME [" + username + "]",  description = "Welcome to the SILENT COAST, a post-apocalyptic city management idle game!")
    embed.add_field(name = "FOUNDING YOUR SETTLEMENT [" + settlementname + "]", value = "To start, you must choose a starting tile for your settlement, be it a coastal trading town or a fortress in the hinterlands. Your starting tile determines your per cycle yields (you get one of each in addition), but it also determines what tiles you're likely to get as you expand, as well as what events you might encounter.", inline = False)
    embed.add_field(name = "-", value = "1. COAST     [FUNDS: 3 INDUSTRY: 1 FOOD: 4 SIZE: 4 DEF: 0]: A higher chance of getting COAST, MARSH, and HILLS tiles", inline = False)
    embed.add_field(name = "-", value = "2. PLAINS    [FUNDS: 2 INDUSTRY: 1 FOOD: 5 SIZE: 6 DEF: -5]: A higher chance of getting PLAINS and FOREST tiles", inline = False)
    embed.add_field(name = "-", value = "3. HILLS     [FUNDS: 1 INDUSTRY: 5 FOOD: 1 SIZE: 3 DEF: 0]: A higher chance of getting HILLS, COAST, and MOUNTAINS tiles", inline = False)
    embed.add_field(name = "-", value = "4. MOUNTAINS [FUNDS: 5 INDUSTRY: 4 FOOD: 0 SIZE: 1 DEF: 10]: A higher chance of getting MOUNTAINS and HILLS tiles", inline = False)
    embed.add_field(name = "-", value = "5. MARSH     [FUNDS: 1 INDUSTRY: 0 FOOD: 7 SIZE: 2 DEF: 15]: A higher chance of getting MARSH, COAST, and FOREST tiles", inline = False)
    embed.add_field(name = "-", value = "6. FOREST    [FUNDS: 2 INDUSTRY: 3 FOOD: 2 SIZE: 3 DEF: 10]: A higher chance of getting FOREST, PLAINS, and HILLS tiles", inline = False)
    embed.add_field(name = "SELECT BELOW", value = "--------------", inline = False)
    return embed