import sys

class Player:
    def __init__(self, line):
        segments = line.split('[')
        try:
            self.number = int(segments[0].rstrip())
            if self.number == 0:
                raise ValueError()

            self.lastname = segments[1].rstrip()[:-1]
            self.firstname = segments[2].rstrip()[:-1]
            self.elo = max(700, int(segments[3].rstrip()[:-1]))
            self.new_elo = self.elo
            self.nb_games = int(segments[4].rstrip()[:-1])
            self.new_nb_games = self.nb_games

            self.weight = self.nb_games
            if self.elo < 800 and self.nb_games > 8:
                self.weight = 8
            elif self.elo < 900 and self.nb_games > 12:
                self.weight = 12
            elif self.nb_games >= 20:
                self.weight = 20

            self.results_str = segments[5].rstrip()[:-1]
            self.results = {}
            self.performance_tmp = self.new_elo
            self.elo_tmp = self.new_elo
            
        except Exception as e:
             print("Players have to follow format 'NUM [LASTNAME][FIRSTNAME][ELO][NB GAMES] [RESULTS]'\n"
                   + f"not '{line}'")
             sys.exit(1)

class Tournament:
    def __init__(self, path):
        with open(path, encoding='utf-8') as file_in:
            lines = file_in.readlines()
            self.nb = 0
            self.name = lines[0][1:-2]
            self.date = lines[1][1:-2]
            self.players = {}
            for i in range (2, len(lines)):
                if lines[i] != '\n':
                    player = Player(lines[i])
                    if self.players.__contains__(player.number):
                        print("Two players have the same number")
                        sys.exit(1)
                    self.players[player.number] = Player(lines[i])

        for _, player in self.players.items():
            games = player.results_str.split(" ")
            for game in games:
                try:
                    opponent = int(game[:-1])
                    if opponent != 0: # num 0 means no opponent
                        if game[-1] != '+' and game[-1] != '-' and game[-1] != '=':
                            raise ValueError()
                        if opponent not in player.results:
                            player.results[opponent] = []
                        win = {'+': 1, '=': 0.5, '-': 0}[game[-1]]
                        player.results[opponent].append(win)
                        player.new_nb_games += 1
                        
                except Exception as e:
                    print(f"Incorrect results format for player {player.number}: '{player.results_str}'")
                    sys.exit(1)
        for _, player in self.players.items():
            for opponent_num, win_list in player.results.items():
                try:
                    opponent = self.players[opponent_num]
                    if len(win_list) != len(opponent.results[player.number]) \
                        or win_list.count(1) != opponent.results[player.number].count(0):
                        raise ValueError()
                except Exception as e:
                    print(f"Match between player {player.number} and player {opponent_num} is not symetric")
                    sys.exit(1)

    def update_elo_tmp(self, player):
        changed = False        
        # Score of new players is updated until it becomes constant
        # Score of other players is only updated at the end
        total_score, total_games, total_wins = 0, 0, 0
        for opponent_num, win_list in player.results.items():
            for win in win_list:
                opponent = self.players[opponent_num]
                if player.nb_games != 0 and opponent.new_elo - player.new_elo > 400 and win == 0:
                    total_score += player.new_elo + 400
                elif player.nb_games != 0 and player.new_elo - opponent.new_elo > 400 and win == 1:
                    total_score += player.new_elo - 400
                else:
                    total_score += opponent.new_elo
                total_games += 1
                total_wins += win
        rate = total_wins / total_games
        player.performance_tmp = total_score / total_games + 800 * (rate - 0.5)

        player.elo_tmp = max(700, (player.elo * player.weight
                          + player.performance_tmp * total_games) \
                         / (player.weight + total_games))

        if player.elo_tmp != player.new_elo:
            changed = True

        return changed

    def calculate_elo(self):
        self.nb += 1
        changed = False
        for _, player in self.players.items():
            if player.results and player.nb_games < 10:
                changed |= self.update_elo_tmp(player)
        if changed: # Iterating gives a new result
            for _, player in self.players.items():
                # elo_tmp is only changed for new players
                player.new_elo = player.elo_tmp
                print(player.new_elo)
            print()
            self.calculate_elo()
        else: # Last iteration is applied to each player
            for _, player in self.players.items():
                if player.results and player.nb_games >= 10:
                    self.update_elo_tmp(player)
            # Update only after every score was calculated
            for _, player in self.players.items():
                player.new_elo = player.elo_tmp + player.new_nb_games - player.nb_games
                player.new_elo = round(player.new_elo)
                player.performance_tmp = round(player.performance_tmp)

def main(arg):
    tournament = Tournament(arg)
    tournament.calculate_elo()
    with open(f"résultats_{arg}", 'w', encoding='utf-8') as file_out:
        file_out.write(f"{tournament.name}\n{tournament.date}\n\n")
        for _, player in tournament.players.items():
            asterisk = '*' if player.nb_games < 10 else ' '
            space1 = (4 - len(str(player.elo))) * ' '
            space2 = (4 - len(str(player.new_elo))) * ' '
            space3 = (4 - len(str(player.performance_tmp))) * ' '
            file_out.write(f"{player.lastname} {player.firstname}\n"
                           + f"\tELO{asterisk} {space1}{player.elo} -> {space2}{player.new_elo} "
                           + f"({space3}{player.performance_tmp})\t"
                           + f"nb parties  {player.nb_games} -> {player.new_nb_games}\n")
        file_out.write("\nParties jouées :\n\n")
        for _, player in tournament.players.items():
            file_out.write(f"{player.lastname} {player.firstname}\n")
            for opponent_num, win_list in player.results.items():
                for win in win_list:
                    opponent = tournament.players[opponent_num]
                    text = "gagne" if win == 1 else "perd" if win == 0 else "fait nulle"
                    file_out.write(f"    {text} contre {opponent.lastname} {opponent.firstname}\n")
        print(f"File 'résultats_{arg}' succesfully saved after {tournament.nb} iterations")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Provide an input file")

#main("shogi.txt")