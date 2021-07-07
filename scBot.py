import discord
from discord.ext import commands
from dotenv import load_dotenv
from scUtil import *
from scFormat import *
import os
import sqlite3
import datetime

# Discord bot stuff init
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='%', guild_subscriptions=True, fetch_offline_members=True, intents=intents)
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
owner = int(os.getenv('OWNER_ID'))

# Database init stuff
db = sqlite3.connect('silentcoast.db')
cursor = db.cursor()

@bot.event
async def on_ready():
    try:

        cursor.execute('CREATE TABLE IF NOT EXISTS users (discord integer PRIMARY KEY, cycleTimer timestamp)')
        # discord: discord user id
        # cycleTimer: datetime used to determine the last time resources were collected


        cursor.execute('CREATE TABLE IF NOT EXISTS settlement (discord integer PRIMARY KEY, name varchar(255), startTerrain varchar(255), population integer DEFAULT 1, fundTotal integer DEFAULT 100, fundRate integer DEFAULT 0, artifactTotal integer DEFAULT 0, artifactRate integer DEFAULT 0, industryRate integer DEFAULT 0, foodRate integer DEFAULT 0, powerRate integer DEFAULT 0, defense integer DEFAULT 0, attack integer DEFAULT 0, totalSlots integer DEFAULT 0, usedSlots integer DEFAULT 0, strange integer DEFAULT 0)')
        # discord: discord user id
        # terrainID: id key string for terrain of settlement
        # population: population of settlement; each pop requires 1 fpc (Food Per Cycle) to live, and the remaining fpc 
        # fundTotal: total money of player; updated upon collection
        # fundRate: money gained per production cycle
        # industryRate: industrial capacity per production cycle, used for construction/production
        # foodRate: food produced per production cycle, used to grow population


        cursor.execute('CREATE TABLE IF NOT EXISTS terrain (id integer PRIMARY KEY, terrainName varchar(255), fundRateMod integer, artifactRateMod integer, industryRateMod integer, foodRateMod integer, powerRateMod integer, size integer, defenseMod integer, weird integer)')
        # id: terrain id
        # terrainName: id key for terrain tile
        # fundRateMod: modifier for funds per cycle
        # industryRateMod: modifier for industrial capacity
        # foodRateMod: modifier for food production
        # size: building slots per terrain

        # GAINING ANY MORE TERRAIN BEYOND THE STARTING TERRAIN REQUIRES 5 POP PER TILE 

        # COAST: higher chance of getting COAST, MARSH, HILLS
        # PLAINS: higher change of getting PLAINS, FOREST
        # HILLS: higher chance of getting HILLS, COAST, MOUNTAINS
        # MOUNTAINS: higher chance of getting MOUNTAINS, HILLS
        # MARSH: higher chance of getting MARSH, COAST, FOREST
        # FOREST: higher chance of getting FOREST, PLAINS, HILLS

        # TODO: Exotic land types e.g. ruined cities, strange terrain (+artifacts)


        cursor.execute('CREATE TABLE IF NOT EXISTS buildings (id integer PRIMARY KEY, buildingName varchar(255), fundCost integer, artifactCost integer, instantBuild integer, icCost integer, fundRateMod integer, artifactRateMod integer, industryRateMod integer, foodRateMod integer, powerRateMod integer, slotsUsed integer, defenseMod integer, attackMod integer, weird integer, tier integer)')
        # id: building id
        # buildingName: id key for building 
        # fundCost: how much the building costs to build
        # artifactCost: how many artifacts does it cost to build, usually 0 for all normal buildings
        # instantBuild: boolean (1/0) on if the building can be built instantly (only for lowest-tier makeshift buildings)
        # icCost: the amount of industry needed to finish the building
        # fundRateMod: modifier for funds per cycle from the building
        # artifactRateMod: modifier for artifacts per cycle from the building (rare, if ever, but here for posterity)
        # industryRateMod: modifier for industrial capacity per cycle
        # foodRateMod: modifier for food production per cycle
        # powerRateMod: modifier for power per cycle
        # slotsUsed: building slots used/required to be free for construction
        # defenseMod: defense added for building
        # attackMod: attack added for building


        cursor.execute('CREATE TABLE IF NOT EXISTS build_q (discord integer PRIMARY KEY, builditemName varchar(255), cost integer, ic integer, startTime timestamp)')
        # discord: discord user id for the build task
        # builditemName: name foreign key for the terrain tile/building being aquired/constructed
        # cost: cost of builditemName
        # ic: industrial capacity of user when construction started
        # startTime: timestamp of when construction started

        # calculation process: 
        # upon collection, if ic * cycles since start >= builditemName cost, remove from this queue table and update settlement
        # else, render progress bar with format barify() and update settlement


        cursor.execute('CREATE TABLE IF NOT EXISTS user_buildings (discord integer PRIMARY KEY, buildingName varchar(255), buildingCount integer)')
        # discord: discord user id of the building owner
        # buildingName: lowercase foreign key for buildings table
        # buildingCount: number of that building that the user has

        # This table stores the player's buildings. Ideally, this isn't accessed in calculation, as every time a building is added it
        # updates the settlement table. This is for recordkeeping and also for additional future checks.

        cursor.execute('CREATE TABLE IF NOT EXISTS user_terrain (discord integer PRIMARY KEY, terrainName varchar(255), terrainCount integer)')
        # discord: discord user id of the building owner
        # terrainName: lowercase foreign key for terrain table
        # terrainCount: number of that terrain tile the user has, INCLUDING THEIR START TILE

        # This table stores the player's buildings. Ideally, this isn't accessed in calculation, as every time a building is added it
        # updates the settlement table. This is for recordkeeping and also for additional future checks.


        # Rebuild non-user tables
        cursor.execute('DELETE FROM terrain')
        cursor.execute('DELETE FROM buildings')

        db.commit()

        csv_to_db("./scTerrain.csv", "terrain", db)
        csv_to_db("./scBuildings.csv", "buildings", db)



    except sqlite3.Error as err:
        print("Databse Error:", err)

    finally:
        print('----------')
        print('Silent Coast Bot Online')
        print(bot.user.id)
        print('----------')


@bot.command(name = 'rebuild', aliases = ['wdb', 'fw', 'w', 'r'], hidden = True)
async def wipe(ctx):
    if ctx.message.author.id == owner:
        rebuild_tables(cursor, db)
    else:
        await ctx.send("VIOLATION: NON-AUTHORIZED USER")


@bot.command(name = 'join', aliases = ['j'], help = 'Name your settlement.')
async def join(ctx, settlementname):

    # if user not in users table, create entry in users and prompt for settlement creation
    cursor.execute('SELECT * FROM users WHERE discord = ?', (ctx.message.author.id,))
    if not cursor.fetchone():

        # insert user into users table (used to track collection times for cycle iteration)
        cursor.execute('INSERT INTO users (discord, cycleTimer) VALUES (?, ?)', (ctx.message.author.id, datetime.datetime.now()))

        # prompt user for starting terrain
        # starting terrain determines starting yield modifiers
        opt1 = '1️⃣'
        opt2 = '2️⃣'
        opt3 = '3️⃣'
        opt4 = '4️⃣'
        opt5 = '5️⃣'
        opt6 = '6️⃣'

        embed = format_join(ctx.message.author.name, settlementname)
        message = await ctx.send(embed=embed)

        await message.add_reaction(opt1)
        await message.add_reaction(opt2)
        await message.add_reaction(opt3)
        await message.add_reaction(opt4)
        await message.add_reaction(opt5)
        await message.add_reaction(opt6)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in [opt1, opt2, opt3, opt4, opt5, opt6]

        reaction, user = await bot.wait_for("reaction_add", check=check)

        if str(reaction.emoji) == opt1:
            await ctx.send('```You have created the settlement of ' + settlementname + " on a rocky seaside outcropping in the SILENT COAST! Use the [collect] command to see your resources.```")
            startTerrain = 'coast'

        if str(reaction.emoji) == opt2:
            await ctx.send('```You have created the settlement of ' + settlementname + " on the inland plains and prairies of the SILENT COAST! Use the [collect] command to see your resources.```")
            startTerrain = 'plains'

        if str(reaction.emoji) == opt3:
            await ctx.send('```You have created the settlement of ' + settlementname + " in the rugged hills of the hinterlands of the SILENT COAST! Use the [collect] command to see your resources.```")
            startTerrain = 'hills'

        if str(reaction.emoji) == opt4:
            await ctx.send('```You have created the settlement of ' + settlementname + " in the jagged peaks that look down upon the SILENT COAST! Use the [collect] command to see your resources.```")
            startTerrain = 'mountains'

        if str(reaction.emoji) == opt5:
            await ctx.send('```You have created the settlement of ' + settlementname + " in the muddy, wet marshlands of the SILENT COAST! Use the [collect] command to see your resources.```")
            startTerrain = 'marsh'

        if str(reaction.emoji) == opt6:
            await ctx.send('```You have created the settlement of ' + settlementname + " in the dark evergreen forests that ring the SILENT COAST! Use the [collect] command to see your resources.```")
            startTerrain = 'forest'

        # add user to settlement table
        cursor.execute('INSERT INTO settlement (discord, name, startTerrain) VALUES (?, ?, ?)', (ctx.message.author.id, settlementname, startTerrain,))
        
        # add starting terrain tile to user_terrain
        cursor.execute('INSERT INTO user_terrain (discord, terrainName, terrainCount) VALUES (?, ?, ?)', (ctx.message.author.id, startTerrain, 1))

        # add govbuilding to user_buildings
        cursor.execute('INSERT INTO user_buildings (discord, buildingName, buildingCount) VALUES (?, ?, ?)', (ctx.message.author.id, "govbuilding", 1))

        db.commit()

        update_settlement(ctx.message.author.id, cursor, db)

    else:

        await ctx.send("```VIOLATION: USER ALREADY EXISTS IN DATABASE```")


@bot.command(name = 'leave', aliases = ['l'], help = 'Leave the game. Your data will be forfeit.')
async def leave(ctx):
    cursor.execute('DELETE FROM users WHERE discord = ?', (ctx.message.author.id,))
    cursor.execute('DELETE FROM settlement WHERE discord = ?', (ctx.message.author.id,))
    cursor.execute('DELETE FROM build_q WHERE discord = ?', (ctx.message.author.id,))
    cursor.execute('DELETE FROM user_terrain WHERE discord = ?', (ctx.message.author.id,))
    cursor.execute('DELETE FROM user_buildings WHERE discord = ?', (ctx.message.author.id,))

    db.commit()

    await ctx.send("```YOU HAVE LEFT THE GAME```")

@bot.command(name = 'collect', aliases = ['c', 'collection', 'col'], help = 'Collects resources and updates progress toward buildings, pop growth etc.')
async def test(ctx):
    
    cursor.execute('SELECT * FROM users WHERE discord = ?', (ctx.message.author.id,))
    if not cursor.fetchone():
        await ctx.send("```VIOLATION: PLEASE JOIN THE GAME BEFORE USING THIS COMMAND```")
        return
    cursor.execute('SELECT * FROM settlement WHERE discord = ?', (ctx.message.author.id,))
    if not cursor.fetchone():
        await ctx.send("```VIOLATION: FINISH SETTLEMENT SET-UP```")
        return

    # determine time difference since last collection in full minuites
    diff = collection_timestamp_update(ctx.message.author.id, cursor, db)

    cursor.execute('SELECT * FROM settlement WHERE discord = ?', (ctx.message.author.id,))
    print(cursor.fetchone())

    # check build progress and save bar

    # update settlements

    # format collect embed
    
    
    
    await ctx.send("ACTION REPORT:\nTIME PASSED SINCE LAST REPORT: "  + str(diff))

@bot.command(name = 'listbuildings', aliases = ['lb', 'bl'], help = 'List buildings. Leave blank for all buildings, or type a number 0-4 for buildings of that tier.')
async def test(ctx, tier = None):
    if tier == None:
        cursor.execute('SELECT * FROM buildings WHERE NOT tier = -1')
        curr = cursor.fetchall()
        print(curr)
    elif tier in ['0', '1', '2', '3', '4']:
        cursor.execute('SELECT * FROM buildings WHERE tier = ?', (tier,))
        curr = cursor.fetchall()
        print(curr)
    else:
        await ctx.send("```VIOLATION: INVALID ARGUMENT TO [listbuildings] COMMAND```")
        

@bot.command(name = 'build', aliases = ['b', 'con', 'const', 'construct', 'constr'], help = 'Construct a building.')
async def test(ctx, building):
    await ctx.send("NOT IMPLEMENTED: SORRY :)")

# Run bot
bot.run(token)
