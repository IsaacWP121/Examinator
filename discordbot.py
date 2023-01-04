import discord, pickle, datetime
from discord.ext import commands
from database import EloDatabase

try:
    with open("config.pkl", "rb") as f:
        prefix = pickle.load(f)[0]
except EOFError:
    prefix = "!"
    with open("config.pkl", "wb") as f:
        pickle.dump([prefix], f)

client = commands.Bot(command_prefix=prefix, intents=discord.Intents.all(), case_insensitive=True)
client.remove_command('help')
data = EloDatabase("database.pkl")
channel_id = []
q = []

async def check(channel_id_input):
    with open("config.pkl", "rb") as f:
        loaded = pickle.load(f)
        try:
            channel_id = loaded[1]
        except IndexError:
            channel_id = loaded[0]

        if channel_id_input in channel_id:
            return True
    return False

@client.command()
async def update_config(ctx, prefix, *channel_ids: int):
    if ctx.permissions.administrator:
        if prefix == "None":
            with open("config.pkl", "rb") as f:
                loaded = pickle.load(f)
                prefix = loaded[0]
        with open("config.pkl", "wb") as f:
            pickle.dump([prefix, channel_ids], f)

        client.command_prefix = prefix
        await ctx.send(f"Prefix: `{prefix}` Channel_Id Whitelist `{channel_ids}`")

@client.command()
async def manual_register(ctx, id_arg):
    if ctx.permissions.administrator:
        await ctx.reply(f"{data.add_player(client.get_user(int(id_arg)))}")

@client.command()
async def create_match(ctx, player_a: str, player_b: str, queued=False):
    if ctx.permissions.administrator or queued:
        def is_mention(string):
            try:
                user = ctx.message.guild.get_member(int(string[2:-1]))
                if user:
                    return True
            finally:
                return False

        try:
            player_a = int(player_a)
        except:
            player_a = int(player_a[2:-1])
        try:
            player_b = int(player_b)
        except:
            player_b = int(player_b[2:-1])

        if data.players.get(player_a) == None or data.players.get(player_b) is None:
            await ctx.send("One or both players are not in the database.")
            return

        # Create an embed message with the player names and reaction buttons for the outcome
        embed = discord.Embed(title=f"Record Match Between {data.players.get(player_a).name} and {data.players.get(player_b).name}", color=0x00ff00)
        embed.add_field(name=f"For {data.players.get(player_a).name} Win", value="Press 🅰️", inline=False)
        embed.add_field(name="For Draw", value="Press 🤝", inline=False)
        embed.add_field(name=f"For {data.players.get(player_b).name} Win", value="Press 🅱️", inline=False)
        embed.add_field(name="\u200b", value=f"{player_a} | {player_b}")
        message = await ctx.send(embed=embed)
        await message.add_reaction("🅰️")  # emoji for a win
        await message.add_reaction("🤝")  # emoji for a draw
        await message.add_reaction("🅱️")  # emoji for a loss

@client.command()
async def unqueue(ctx):
    if await check(ctx.channel.id):
        try:
            if ctx.message.author.id in data.players:
                if ctx.message.author.id in q:
                    q.remove(ctx.message.author.id)
                    await ctx.reply("You have been removed from the queue.")
                else:
                    await ctx.reply("You are not in the the queue.")
            else:
                await ctx.reply(content=("You are not registered in the database yet, use"+" !register "+"to register."))
        except Exception as e:
            # Log the error
            print(datatime.datetime.utcnow() + " | " + e)
            # Send a message to the user informing them that something went wrong
            await ctx.send("An error occurred while processing your request. Please try again later.")

@client.command()
async def queue(ctx):
    if await check(ctx.channel.id):
        try:
            if ctx.message.author.id in data.players:
                if ctx.message.author.id in q:
                    await ctx.reply("You are already in the queue.")
                else:
                    q.append(ctx.message.author.id)
                    await ctx.reply("You have been added to the queue.")

                if len(q) >= 2:
                    player_a = q.pop(0)
                    player_b = q.pop(0)
                    await create_match(ctx, player_a, player_b, queued=True)
            else:
                await ctx.reply(content=("You are not registered in the database yet, use"+" !register "+"to register."))
        except Exception as e:
            # Log the error
            print(datatime.datetime.utcnow() + " | " + e)
            # Send a message to the user informing them that something went wrong
            await ctx.send("An error occurred while processing your request. Please try again later.")

@client.command()
async def register(ctx):
    if await check(ctx.channel.id):
        await ctx.reply(f"{data.add_player(ctx.message.author)}")

@client.command()
async def rating(ctx, *mentions):
    if await check(ctx.channel.id):
        if len(mentions) == 0:
            embed = discord.Embed(color=0x00ff00)
            embed.add_field(name=f"{data.get_rating(ctx.message.author.id)[1]} Rating:", value=f"{round(data.get_rating(ctx.message.author.id)[0])}", inline=False)         
            await ctx.reply(embed=embed)

        else:
            embed = discord.Embed(color=0x00ff00)
            for i in mentions:
                embed.add_field(name=f"{data.get_rating(int(i[2:-1]))[1]} Rating:", value=f"{data.get_rating(int(i[2:-1]))[0]}", inline=False)          
            await ctx.reply(embed=embed)

@client.command()
async def leaderboard(ctx):
    if await check(ctx.channel.id):
        await ctx.send(embed=data.get_leaderboard())

@client.command()
async def help(ctx):
    if await check(ctx.channel.id):
        embed = discord.Embed(title="Available Commands", color=0x00ff00)
        if ctx.permissions.administrator:
            embed.title = "Available Commands (Admin Included)"
            embed.add_field(name="update_config", value="Updates the bot's configuration. (Admin Only)", inline=False)
            embed.add_field(name="manual_register", value="Manually registers a new player in the database. (Admin Only)", inline=False)
            embed.add_field(name="create_match", value="Manually creates a new match between two players. (Admin Only)", inline=False)
        embed.add_field(name="help", value="Shows this help message.", inline=False)
        embed.add_field(name="register", value="Registers a new player in the database.", inline=False)
        embed.add_field(name="rating", value="Allows you to view the rating of the sender. `rating @user @user2 @user3...` allows for you to check multiple discord user's ratings", inline=False)
        embed.add_field(name="leaderboard", value="Displays the leaderboard of players and their Elo ratings.", inline=False)
        embed.add_field(name="queue", value="Adds the user to the queue for a match.", inline=False)
        embed.add_field(name="unqueue", value="Removes the user from the queue.", inline=False)
        await ctx.send(embed=embed)

@client.event
async def on_command_error(ctx, error):
    if await check(ctx.channel.id):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Invalid command. Try !help for a list of available commands.")

@client.event
async def on_reaction_add(reaction, user):
    if await check(reaction.message.channel.id):
        try:
            if user.id != client.user.id and reaction.message.author.id == client.user.id and "Record" in reaction.message.embeds[0].title.split()[0]:
                players = [int(player_id) for player_id in reaction.message.embeds[0].fields[len(reaction.message.embeds[0].fields)-1].value.split(" | ")]
                if user.id in players:
                    if reaction.emoji == "🅰️":
                        outcome_value = 1
                    elif reaction.emoji == "🤝":
                        outcome_value = 0.5
                    elif reaction.emoji == "🅱️":
                        outcome_value = 0
                    else:
                        await ctx.send("Invalid outcome.")
                        return

                    await reaction.message.clear_reactions()
                    data.record_match(int(players[0]), int(players[1]), outcome_value)
                    await reaction.message.reply(f"Match between {data.players.get(int(players[0])).name} and {data.players.get(int(players[1])).name} recorded.\nElo's can be checked using {client.command_prefix}rating\nLeaderboard can be checked with {client.command_prefix}leaderboard")
        except:
            pass

# Run the bot with the specified token
client.run("MTAzMTUxOTE4MDYzOTQ1MzE5NQ.GuqBZg.hTkSMoaDLEo0gbyiKOBc9g03s9poWqKFybZRO0")