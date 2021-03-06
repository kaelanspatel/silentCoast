import discord
from discord.ext import commands
from dotenv import load_dotenv
from scUtil import *
from scFormat import *
import asyncio
import os
import sqlite3
import datetime
import string

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

building_names = csv_to_dict("./scBuildingNames.csv")

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


        cursor.execute('CREATE TABLE IF NOT EXISTS user_buildings (discord integer, buildingName varchar(255), buildingCount integer)')
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

        await cycler()


@bot.command(name = 'rebuild', aliases = ['wdb', 'fw', 'w', 'r'], hidden = True)
async def wipe(ctx):
    if ctx.message.author.id == owner:
        rebuild_tables(cursor, db)
    else:
        await ctx.send("```VIOLATION: NON-AUTHORIZED USER```")


@bot.command(name = 'join', aliases = ['j'], help = 'Name your settlement.')
async def join(ctx, settlementname = None):

    if settlementname == None:
        await ctx.send("```VIOLATION: SPECIFY A SETTLEMENT NAME```")

    # 32 char limit, as arbitrarily set by me :V
    # strip punctuation; thanks Alex :)
    settlementname = settlementname[:32]
    settlementname.translate(str.maketrans('', '', string.punctuation))

    # if user not in users table, create entry in users and prompt for settlement creation
    cursor.execute('SELECT * FROM users WHERE discord = ?', (ctx.message.author.id,))
    if not cursor.fetchone():

        # insert user into users table (used to track collection times for cycle iteration)
        cursor.execute('INSERT INTO users (discord, cycleTimer) VALUES (?, ?)', (ctx.message.author.id, datetime.datetime.now()))

        # prompt user for starting terrain
        # starting terrain determines starting yield modifiers
        opt1 = '1??????'
        opt2 = '2??????'
        opt3 = '3??????'
        opt4 = '4??????'
        opt5 = '5??????'
        opt6 = '6??????'

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
            await ctx.send('```You have created the settlement of ' + settlementname + " atop a rocky seaside outcropping on the SILENT COAST! Use the [collect] command to see your resources.```")
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

        update_settlement(ctx.message.author.id, cursor, db, 0)

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

@bot.command(name = 'status', aliases = ['s', 'stats'], help = 'Check settlement status (building/growth progress, resources etc).')
async def test(ctx):
    
    cursor.execute('SELECT * FROM users WHERE discord = ?', (ctx.message.author.id,))
    if not cursor.fetchone():
        await ctx.send("```VIOLATION: PLEASE JOIN THE GAME BEFORE USING THIS COMMAND```")
        return

    # determine time difference since last collection in full minuites and update
    diff = collection_timestamp_update(ctx.message.author.id, cursor, db)
    
    cursor.execute('SELECT * FROM settlement WHERE discord = ?', (ctx.message.author.id,))
    user_row = cursor.fetchone()
    if not user_row:
        await ctx.send("```VIOLATION: FINISH SETTLEMENT SET-UP```")
        return
    
    # update settlement totals
    update_settlement(ctx.message.author.id, cursor, db, diff)

    cursor.execute('SELECT * FROM settlement WHERE discord = ?', (ctx.message.author.id,))
    user_row = cursor.fetchone()

    # check build progress and save bar
    cursor.execute('SELECT builditemName FROM build_q WHERE discord = ?', (ctx.message.author.id,))
    builditem = cursor.fetchone()

    if builditem:

        builditem = builditem[0]

        if builditem in building_names:
            icbar = update_buildq(ctx.message.author.id, cursor, db, builditem)
            embed = format_status(user_row, icbar, '', True, builditem)

            await ctx.send(embed = embed)
            

    else:

         embed = format_status(user_row, '', '', False, None)
         await ctx.send(embed = embed)
    
    
    # await ctx.send("ACTION REPORT:\nTIME PASSED SINCE LAST REPORT: "  + str(diff))

@bot.command(name = 'listbuildings', aliases = ['lb', 'bl'], help = 'List buildings. Leave blank for all buildings, or type a number 0-4 for buildings of that tier.')
async def test(ctx, tier = None):
    if tier == None:
       await ctx.send("```VIOLATION: CORRECT USAGE IS [%listbuildings] AND THEN A TIER 0-4```")
    elif tier in ['0', '1', '2', '3', '4']:
        cursor.execute('SELECT * FROM buildings WHERE tier = ?', (tier,))
        buildings = cursor.fetchall()
        await ctx.send(embed = format_buildinglist(buildings, tier))
    else:
        await ctx.send("```VIOLATION: INVALID ARGUMENT TO [%listbuildings] COMMAND```")
        

@bot.command(name = 'build', aliases = ['b', 'con', 'const', 'construct', 'constr'], help = 'Construct a building.')
async def test(ctx, building = None):
    if building == None:
        await ctx.send("```VIOLATION: NO BUILDING SPECIFIED, DESIGNATE A BUILDING BUILD STRING```")
        return
    
    if len(building) > 20:
        await ctx.send("```VIOLATION: INVALID BUILD STRING```")
        return

    cursor.execute('SELECT * FROM buildings WHERE buildingName = ?', (building,))
    tobuild = cursor.fetchone()

    if not tobuild:

        await ctx.send("```VIOLATION: INVALID BUILD STRING```")
        return

    else:

        cost = tobuild[2]
        acost = tobuild[3]
        slots = tobuild[11]
        iccost = tobuild[5]
        
        cursor.execute('SELECT name, industryRate FROM settlement WHERE discord = ?', (ctx.message.author.id,))
        userdata = cursor.fetchone()
        settlement_name = userdata[0]
        user_ic = userdata[1]

        yes = '???'
        no = '???'

        embed = format_build(building, tobuild)
        message = await ctx.send(embed=embed)

        await message.add_reaction(yes)
        await message.add_reaction(no)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in [yes, no]

        reaction, user = await bot.wait_for("reaction_add", check=check)

        if str(reaction.emoji) == yes:

            building_blocked = can_build(ctx.message.author.id, cursor, cost, acost, slots)

            if building_blocked:
                await ctx.send("```VIOLATION: " + building_blocked + "```")
                return
            else:
                
                # subtract funds/artifacts required
                print(type(cost), type(acost))
                cursor.execute('UPDATE settlement SET fundTotal = fundTotal - ?, artifactTotal = artifactTotal - ? WHERE  discord = ?', (cost,acost,ctx.message.author.id,))

                # add building to build queue
                cursor.execute('INSERT INTO build_q (discord, builditemName, cost, ic, startTime) VALUES (?, ?, ?, ?, ?)', (ctx.message.author.id, building, iccost, user_ic, datetime.datetime.now(),))
                await ctx.send("```BEGINNING CONSTRUCTION IN THE SETTLEMENT OF " + settlement_name + "```")

                # in the case of a tier 0 building, the construction will already be done, so do a quick update
                # this should just default to nothing for any other building, because no time has passed.
                bar = update_buildq(ctx.message.author.id, cursor, db, building)
                update_settlement(ctx.message.author.id, cursor, db, 0)
                print(bar)

        if str(reaction.emoji) == no:
            
            await ctx.send("```CONSTRUCTION CANCELED```")
            
async def cycler():
    while True:

        cursor.execute('SELECT discord FROM users')
        users = cursor.fetchall()
        print(users)
        for user in users:

            user = user[0]
            
            # determine time difference since last collection in full minuites and update
            diff = collection_timestamp_update(user, cursor, db)
            
            # update settlement totals
            update_settlement(user, cursor, db, diff)

            cursor.execute('SELECT * FROM settlement WHERE discord = ?', (user,))
            user_row = cursor.fetchone()

            # check build progress and save bar
            cursor.execute('SELECT builditemName FROM build_q WHERE discord = ?', (user,))
            builditem = cursor.fetchone()

            if builditem:

                builditem = builditem[0]

                if builditem in building_names:
                    update_buildq(user, cursor, db, builditem)

        await asyncio.sleep(300)

# Run bot
bot.run(token)
