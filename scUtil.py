import datetime, pandas

# Get difference between row with key discord's last collection time and now
def get_cycle_difference(discord, cursor):
    cursor.execute('SELECT * FROM users WHERE discord = ?', (discord,))
    if not cursor.fetchone():
        print("Error in get_cycle_difference: user does not exist in table!")

        return -1
    else:
        cursor.execute('SELECT CAST ((JulianDay(?) - JulianDay(cycleTimer)) * 24 * 60  As Integer) FROM users WHERE discord = ?', (datetime.datetime.now(), discord,))
        diff = cursor.fetchone()

        cursor.execute('SELECT cycleTimer FROM users WHERE discord = ?', (discord,))
        curr = cursor.fetchone()

        print(diff, curr, datetime.datetime.now())
        return int(diff[0])

# Update cycleTimer of row with key discord to current time
def update_cycle_timer(discord, cursor, db):
    cursor.execute('SELECT * FROM users WHERE discord = ?', (discord,))
    if not cursor.fetchone():
        print("Error in update_cycle_timer: user does not exist in table!")

    else:
        cursor.execute('UPDATE users SET cycleTimer = ? WHERE discord = ?', (datetime.datetime.now(), discord,))
        db.commit()

# Get time passed since last collection and update collection to current time
def collection_timestamp_update(discord, cursor, db):
    diff = get_cycle_difference(discord, cursor)
    if diff < 0:
        return -1

    else:
        update_cycle_timer(discord, cursor, db)
        return diff

# Loads csv of filename into tablename table in db
def csv_to_db(filename, tablename, db):
    df = pandas.read_csv(filename)
    df.to_sql(tablename, db, if_exists='append', index=False)
    db.commit()

# Updates all settlement rows for key discord based on table user_buildings and user_terrain
def update_settlement(discord, cursor, db):

    # check build queue
    # TODO

    # update totals
    cursor.execute('SELECT fundRate, artifactRate FROM settlement WHERE discord = ?', (discord,))
    to_add = [int(item) for item in cursor.fetchone()]

    cursor.execute('UPDATE settlement SET fundTotal = fundTotal + ?, artifactTotal = artifactTotal + ? WHERE discord = ?', (to_add[0], to_add[1], discord,))

    # access user_terrain and get all terrains associated with user
    cursor.execute('SELECT terrainName, terrainCount FROM user_terrain WHERE discord = ?', (discord,))
    terrains = cursor.fetchall()

    # access user_buildings and get all buildings associated with user
    cursor.execute('SELECT buildingName, buildingCount FROM user_buildings WHERE discord = ?', (discord,))
    buildings = cursor.fetchall()

    for terrain, count in terrains:
        cursor.execute('SELECT fundRateMod, artifactRateMod, industryRateMod, foodRateMod, powerRateMod, size, defenseMod, weird FROM terrain WHERE terrainName = ?', (terrain,))
        tmodifiers = [int(int(item) * int(count)) for item in cursor.fetchone()]

        cursor.execute('UPDATE settlement SET fundRate = fundRate + ?, artifactRate = artifactRate + ?, industryRate = industryRate + ?, foodRate = foodRate + ?, powerRate = powerRate + ?, defense = defense + ?, totalSlots = totalSlots + ?, strange = strange + ? WHERE  discord = ?', (tmodifiers[0],tmodifiers[1],tmodifiers[2],tmodifiers[3],tmodifiers[4],tmodifiers[6],tmodifiers[5],tmodifiers[7],discord,))

    for building, count in buildings:
        cursor.execute('SELECT fundRateMod, artifactRateMod, industryRateMod, foodRateMod, powerRateMod, slotsUsed, defenseMod, attackMod, weird FROM buildings WHERE buildingName = ?', (building,))
        bmodifiers = [int(int(item) * int(count)) for item in cursor.fetchone()]

        cursor.execute('UPDATE settlement SET fundRate = fundRate + ?, artifactRate = artifactRate + ?, industryRate = industryRate + ?, foodRate = foodRate + ?, powerRate = powerRate + ?, defense = defense + ?, attack = attack + ?, totalSlots = totalSlots + ?, strange = strange + ? WHERE  discord = ?', (bmodifiers[0],bmodifiers[1],bmodifiers[2],bmodifiers[3],bmodifiers[4],bmodifiers[6],bmodifiers[7],bmodifiers[5],bmodifiers[8],discord,))

    db.commit()


# Deletes and recreates empty tables
def rebuild_tables(cursor, db):
    cursor.execute('DROP TABLE users')
    cursor.execute('DROP TABLE settlement')
    cursor.execute('DROP TABLE terrain')
    cursor.execute('DROP TABLE buildings')
    cursor.execute('CREATE TABLE IF NOT EXISTS users (discord integer PRIMARY KEY, cycleTimer timestamp)')
    cursor.execute('CREATE TABLE IF NOT EXISTS settlement (discord integer PRIMARY KEY, name varchar(255), startTerrain varchar(255), population integer DEFAULT 1, fundTotal integer DEFAULT 100, fundRate integer DEFAULT 0, artifactTotal integer DEFAULT 0, artifactRate integer DEFAULT 0, industryRate integer DEFAULT 0, foodRate integer DEFAULT 0, powerRate integer DEFAULT 0, defense integer DEFAULT 0, attack integer DEFAULT 0, totalSlots integer DEFAULT 0, usedSlots integer DEFAULT 0, strange integer DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS terrain (id integer PRIMARY KEY, terrainName varchar(255), fundRateMod integer, artifactRateMod integer, industryRateMod integer, foodRateMod integer, powerRateMod integer, size integer, defenseMod integer, weird integer)')
    cursor.execute('CREATE TABLE IF NOT EXISTS buildings (id integer PRIMARY KEY, buildingName varchar(255), fundCost integer, artifactCost integer, instantBuild integer, icCost integer, fundRateMod integer, artifactRateMod integer, industryRateMod integer, foodRateMod integer, powerRateMod integer, slotsUsed integer, defenseMod integer, attackMod integer, weird integer, tier integer)')
    db.commit()