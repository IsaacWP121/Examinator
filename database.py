import pickle, math, discord, traceback, time

class Player:
    def __init__(self, name, userid, rating=1200):
        self.name = name
        self.rating = rating
        self.userid = userid
        self.record = {'W': 0, 'L': 0, 'D': 0}
        self.opponents = []

    def __str__(self):
        return f'Player Name:{self.name}, Player Rating:{self.rating}, Player UserID:{self.userid}, Player Record:{self.record}, Player opponents:{self.opponents}'

def expected_outcome(rating_a, rating_b):
    return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))

def update_rating(rating, outcome, expected):
    return rating + 50 * (outcome - expected)

class EloDatabase:
    def __init__(self, databasefile):
        self.databasefile = databasefile
        self.updated = {} # formatted as {user_id:time}
        with open(self.databasefile, "rb") as f:
            try:
                self.players = pickle.load(f)
            except:
                self.players = {}

    def backup(self):
        with open(self.databasefile, "wb") as f:
            pickle.dump(self.players, f)

    def add_player(self, user):
        try:
            if self.players[user.id] != None:
                self.backup()
            return f"{user.name} already added."
        finally:
            self.players[user.id] = Player(user.name, user.id)
            self.backup()
            return f"{user.name} has been added!"

    def record_match(self, player_a_id, player_b_id, outcome):
        # add the opponents to each player's list of opponents
        player_a = self.players.get(player_a_id)
        player_b = self.players.get(player_b_id)
        player_a.opponents.append(player_b.userid)
        player_b.opponents.append(player_a.userid)

        # calculate the expected outcome for each player
        expected_a = expected_outcome(player_a.rating, player_b.rating)
        expected_b = expected_outcome(player_b.rating, player_a.rating)

        # update the ratings of each player based on the outcome of the match
        player_a.rating = update_rating(player_a.rating, outcome, expected_a)
        player_b.rating = update_rating(player_b.rating, 1 - outcome, expected_b)

        # update the record of each player based on the outcome of the match
        if outcome == 1:
            player_a.record['W'] += 1
            player_b.record['L'] += 1
        elif outcome == 0:
            player_a.record['L'] += 1
            player_b.record['W'] += 1
        else:
            player_a.record['D'] += 1
            player_b.record['D'] += 1
        # save the updated players to the file
        self.updated[player_a_id] = time.time()
        self.updated[player_b_id] = time.time()
        self.backup()

    def get_rating(self, player_id):
        return self.players[player_id].rating, self.players[player_id].name

    def dev_dump(self, player_id=None):
        return self.players[next((player for player in self.players if self.players.userid == player_id), None)]

    def get_leaderboard(self):
        leaderboard = sorted(self.players.values(), key=lambda x: -x.rating)
        
        embed = discord.Embed(title="Leaderboard", color=0x00ff00)
        # add the leaderboard data to the embed
        for i, player in enumerate(leaderboard):
            embed.add_field(name=f'{i+1}. {player.name}', value=round(player.rating), inline=True)
        return embed