#########################################
#       Creator: Nicola Ricciardi       #
#       Version: 1.0.0                  #
#########################################


import json
from datetime import datetime

class DBChessAnalizer:
    """"""

    def __init__(self, db_file_name='input.pgn', output_name='output.json'):
        """Constructor for DBChessAnalizer"""

        # imposto il nome del file del database
        self.__db_file_name = db_file_name
        # imposto il nome del file in cui stampare l'output
        self.__output_name = output_name

    # carico il database
    def __load(self,
               db_file_name=None):  # se il db_file_name prende valore None, utilizzo il nome del database istanziato nel costruttore

        self.__db_file = None

        # provo a caricare il database di input
        try:
            if db_file_name == None:
                self.__db_file = open(self.__db_file_name, 'r')
            else:
                self.__db_file = open(db_file_name, 'r')
        except Exception as e:
            print("Missing database file")

    # scrive lo stringa passata in un file di testo con il nome passato
    def __write_in_file(self, data="", name="output.txt"):
        file = open(name, "w")      # apro/creo il file
        file.write(data)
        file.close()

    # genera l'output
    def generate_json(self, db_file_name=None, output_name=None, max_matches=None):

        # carico il database
        if db_file_name != None:
            self.__db_file_name = db_file_name
        self.__load(db_file_name)

        # imposto il nome all'output
        if output_name != None:
            self.__output_name = output_name

        self.__close()      # chiudo il file contenente il db

        # converto le partite del database in un array
        parsed_matches = self.__parse_pgn_matches(max_matches)

        # istanzio il nuovo database in formato json
        json_db = {
            "n_match_played": len(parsed_matches),      # inserisco il numero di match giocati
            "matches": parsed_matches,                  # inserisco i match giocati
            "win_rates": self.__get_win_rates(parsed_matches),   # inserisco i dati statistici
            "tree": self.__generate_tree(parsed_matches, 0, 1)     # creo l'albero delle aperture
        }

        # scrivo il json nel file
        self.__write_in_file(json.dumps(json_db), self.__output_name)

        return json_db

    # genera l'albero delle aperture. Esempio:
    # [
    #     {
    #         "piece": "p",     !!!
    #         "move": "e5",
    #         "analysis": {         !!!
    #             "eval": 0.38,
    #             "depth": 43
    #         },
    #         "winnings": {
    #                         "white": {
    #                             "total": 0,
    #                             "rate": 0
    #                         },
    #                         "black": {
    #                             "total": 0,
    #                             "rate": 0
    #                         },
    #                         "draw": {
    #                             "total": 0,
    #                             "rate": 0
    #                         }
    #                     },
    #         "gamesPlayed": 17784551,
    #         "lastPlayed": 2021
    #
    #     },
    #     {
    #         ...
    #     }
    # ]

    # parametri:
    # move --> indica la mossa, ossia 1, 2, 3, ...
    # semiove --> indica la semimossa, ossia white/black
    # pre_move --> indica la mossa precedentemente effettuata, se non presente: inizio partita
    # in combinazione diventa: (1, white), (1, black), (2, white), ...
    def __generate_tree(self, matches, n_move, semimove, pre_moves = None):

        if pre_moves == None:
            firstCall = True
        else:
            firstCall = False

        if semimove == 1:       # converto le semimosse in white/black, successivamente aggiorno il valore per la semimossa successiva e il valore della mossa successiva
            player = "white"
            pre_player = "black"
            semimove = 2
            add_move = 0            # valore da aggiungere a n_move al richiamo della funzione ricorsiva
            remove_to_pre_move = 1      # valore da togliere alla premossa durante il filtraggio
        elif semimove == 2:
            player = "black"
            pre_player = "white"
            semimove = 1
            add_move = 1
            remove_to_pre_move = 0

        # DEBUG:
        # print("First call? ", firstCall)
        # print("Move n. ", n_move)
        # print("Player: ", player)
        # print("Premoves: ", pre_moves)
        # print("------------")

        next_moves = []           # variabile contenente l'albero delle mosse successive
        moves_played = []       # variabile di appoggio in cui salvo tutte le mosse giocate per non ripeterle nell'array finale


        for match in matches:               # scorro tutti i match semimossa per semimossa analizzandoli
            try:
                # creo la variabile (pre_moves_list_to_check) da utilizzare durante il controllo delle mosse precendenti in quanto pre_moves non contiene l'ulitma mossa fatta (__get_move_list restituisce una mossa in più; per fixare aggiungo l'ultima mossa al controllo)
                pre_moves_list_to_check = None
                if isinstance(pre_moves, list):
                    pre_moves_list_to_check = pre_moves.copy()
                if isinstance(pre_moves_list_to_check, list):
                    pre_moves_list_to_check.append(match["moves"]["list"][n_move][player])      # se tutti i controlli vanno a buon fine genero la lista da utilizzare con l'ultima mossa fatta

                if firstCall or self.__check_move_match(self.__get_move_list(match=match, end=((n_move - remove_to_pre_move) * 2) + semimove), pre_moves_list_to_check): #or match["moves"]["list"][n_move - remove_to_pre_move][pre_player] == pre_move:              # se è stata passata una pre_move (modalità ricorsione), controllo che la mossa precedente corrisponda prima di salvare la mossa
                    move_played = match["moves"]["list"][n_move][player]     # salvo ogni semimossa fatta (es. (1, white))
                else:
                    continue
            except Exception as error:
                continue

            # trasformo pre_move in un array vuoto se è nella prima chiamata in modo da salvare le mosse successive
            if firstCall:
                pre_moves = []

            # inserisco la mossa effetuata nell'array delle mosse precedenti per il richiamo successivo
            if isinstance(pre_moves, list):
                pre_moves_to_use = pre_moves.copy()     # genero una nuova variabile per non sporcare pre_moves per i cicli successivi
                pre_moves_to_use.append(move_played)


            if move_played not in moves_played:         # se la mossa effettuata non è nell'array di controllo delle mosse già effettuate
                # creo il nuovo oggetto rappresentante la mossa
                new_move = {
                    "piece": None,
                    "move": move_played,
                    "analysis": {
                        "eval": 0,
                        "depth": 0
                    },
                    "winnings": {
                        "white": {
                            "total": 0,
                            "rate": 0
                        },
                        "black": {
                            "total": 0,
                            "rate": 0
                        },
                        "draw": {
                            "total": 0,
                            "rate": 0
                        }
                    },
                    "gamesPlayed": 0,
                    "lastPlayed": "0001.01.01",           # data default 0001.01.01   Y.m.d
                    "nextMoves": None
                }

                # aggiungo l'oggetto mossa all'elenco delle mosse
                next_moves.append(new_move)

            # cerco la mossa effettuata nel match nell'array delle mosse e ne incremento i valori
            for index in range(len(next_moves)):
                if next_moves[index]["move"] == move_played:    # trovo l'oggetto mossa analoga alla mossa effetuata in questo match
                    next_moves[index]["gamesPlayed"] += 1       # incremento il numero di match giocati

                    # aggiorno la data
                    this_match_date = datetime.strptime(match["Date"], '%Y.%m.%d').date()       # converto la data in un oggetto manipolabile
                    if datetime.strptime(next_moves[index]["lastPlayed"], '%Y.%m.%d').date()  < this_match_date:       # se la data del match corrente è maggiore, la sostituisco
                        next_moves[index]["lastPlayed"] = this_match_date.strftime("%Y.%m.%d")


                    next_moves[index]["winnings"][match["Result"]["winner"]]["total"] += 1          # aggiungo una vincita al giocatore vincitore con quella mossa

                    # inserisco il pezzo che ha effettuato la mossa
                    next_moves[index]["piece"] = self.__get_piece(move_played)

                    # ricalcolo le percentuali di vittoria/pareggio/sconfitta
                    next_moves[index]["winnings"]["white"]["rate"] = next_moves[index]["winnings"]["white"]["total"] * 100 / next_moves[index]["gamesPlayed"]
                    next_moves[index]["winnings"]["black"]["rate"] = next_moves[index]["winnings"]["black"]["total"] * 100 / next_moves[index]["gamesPlayed"]
                    next_moves[index]["winnings"]["draw"]["rate"] = next_moves[index]["winnings"]["draw"]["total"] * 100 / next_moves[index]["gamesPlayed"]


                    next_moves_generated = self.__generate_tree(matches, n_move + add_move, semimove, pre_moves_to_use.copy())        # genero ricorsivamente le prossime mosse
                    if next_moves_generated == []:
                        next_moves[index]["nextMoves"] = None
                    else:
                        next_moves[index]["nextMoves"] = next_moves_generated


            moves_played.append(move_played)     # per mossa giocata, aggiungo quest'ultima all'array delle mosse giocate per poi effettuare il controllo al prossimo ciclo (controllo: che la stessa mossa non sia già stata effettuata in un altro match)

        # restituisco l'albero delle mosse
        return next_moves

    # restituisce True se le due seguenze di mosse corrispondono, formato: ["e4", "e5", ...]
    def __check_move_match(self, moves1, moves2):
        return moves1 == moves2

    # resistuisce sotto forma di array, le mosse effettuate in un match
    def __get_move_list(self, match, start=None, end=None):
        moves_list = match["moves"]["list"]     # variabile contenente le mosse effettuate durante il match nel formato classico

        new_moves_list = []                     # variabile contenente le mosse effettuate durante il match nel formato stringa; ["e4", "e5", ...]

        for move in moves_list:
            for player in ["white", "black"]:
                new_moves_list.append(move[player])

        if end != None:     # aggiungo 1 all'end in modo da fixare gli estremi
            end += 1

        return new_moves_list[start:end]        # resituisco l'array da start a end


    # restituisce il pezzo usato durante la mossa passata
    def __get_piece(self, move):

        if move == None:
            return

        PIECES = "KQRBN0"

        if move[0] not in PIECES:
            return "P"
        else:
            if move[0] == "0":
                return "K"
            else:
                return move[0]

    # calcolo le percentuali di vittoria
    def __get_win_rates(self, matches):

        # variabili di appoggio per contare le percentuali di vittoria
        white_win = []
        black_win = []
        draw = []

        try:        # calcolo il numero di partite vinte/pareggiate
            for match in matches:
                if match["Result"]["winner"] == "white":
                    white_win.append(match["id"])
                elif match["Result"]["winner"] == "black":
                    black_win.append(match["id"])
                elif match["Result"]["winner"] == "draw":
                    draw.append(match["id"])
        except Exception as e:
            pass

        # calcolo il numero di match
        n = len(matches)

        # istanzio il risultato del metodo
        try:
            result = {
                "white": {
                    "wins": len(white_win),
                    "rate": len(white_win)*100/n
                },
                "black": {
                    "wins": len(black_win),
                    "rate": len(black_win)*100/n
                },
                "draw": {
                    "wins": len(draw),
                    "rate": len(draw)*100/n
                }
            }
        except Exception as e:
            pass

        return result

    # converto un pgn in dizionario
    def __parse_pgn_matches(self, max_matches=None):

        # scorro il database riga per riga
        matches = [] # array contenente tutte le partite (return)
        match = ""  # variabile (str) di appoggio in cui saranno inserite le singole partite
        id = 1      # tiene conto degli id da inserire
        for row in self.__db_file:

            match += str(row)

            if row[0] == "1":           # se la riga inizia con 1, quindi è la riga delle mosse, riavvio
                matches.append(self.__parse_single_pgn_match(match, {"id": id}))    # inserisco il nuovo match convertito
                id += 1     # incremento l'id
                match = ""

                # scalo di 1 il massimo dei match utilizzabili
                if max_matches != None:
                    max_matches -= 1
                    if max_matches <= 0:  # se arriva al massimo dei match da utilizzare, interrompe il ciclo
                        break

        return matches

    # restituisce un dizionario rappresentante la partita
    def __parse_single_pgn_match(self, pgn_match_str, union = {}):
        match = {}  # variabile di appoggio in cui saranno inserite le singole partite

        pgn_match_str_array = pgn_match_str.split("\n")

        for row in pgn_match_str_array:
            if row.find("[") != -1:  # se è presente una [
                # elimino le []
                row = row.replace("[", "")
                row = row.replace("]", "")

                # divido la riga
                row_split = row.split(" ")

                # salvo le informazioni
                value = ""
                for p in range(1, len(row_split)):
                    value += str(row_split[p])

                value = value.replace('"', '')

                match[row_split[0]] = value  # salvo il valore finale
            elif row.find("1.") != -1:  # se la riga non è vuota e contiene il carattere della prima mossa
                if row.strip() != "":
                    match["moves"] = {
                        "str": row,
                        "list": self.__parse_moves(row)
                    }

        # inserisco il campo winner
        try:
            match_result = match["Result"].split("-")       # creo un array contenete il risultato
            winner = None

            # comprato e genero il vincitore
            if match_result[0] > match_result[1]:
                winner = "white"
            elif match_result[0] < match_result[1]:
                winner = "black"
            elif match_result[0] == match_result[1]:
                winner = "draw"

            if winner != None:
                match["Result"] = {
                    "winner": winner,
                    "result": match["Result"]
                }

        except Exception as e:
            pass

        # unisco le informazioni aggiuntive passate
        try:
            match.update(union)
        except Exception as e:
            pass

        return match

    # converte le mosse (str) in formato [{}, {}, ...]
    def __parse_moves(self, moves):
        moves_array = moves.split(' ')  # creo un array in cui in saranno inserite le varie mosse e il numero di mossa
        moves_array_dict = []  # creo un array che conterrà un {} per ogni mossa, il dizionario conterrà 3 attributi: n, w, b (numero di mossa, mossa del bianco, mossa del nero)
        for i in range(len(moves_array)):
            if i % 3 == 0:  # ogni volta che si incontra il numero di mossa, legge i successivi due (mossa del bianco e mossa del nero)
                move_dict = {}  # creo il dizionario che conterrà le informazioni

                # inserisco le informazioni al suo interno
                try:
                    if isinstance(int(moves_array[i][0:-1]),
                                  int):  # controllo che sia una mossa valida: se i prini n-1 caratteri della stringa sono un numero significa che è una mossa
                        move_dict["move"] = moves_array[i]
                    else:
                        break

                    # istanzio le mosse del bianco
                    move_dict["white"] = moves_array[i + 1]

                    # istanzio le mosse del nero
                    if moves_array[i + 2].find("{") == -1 and moves_array[i + 2].find("}") == -1 and moves_array[i + 2].find("-") == -1:
                        move_dict["black"] = moves_array[i + 2]
                    else:
                        move_dict["black"] = None

                except Exception as e:
                    break

                # aggiungo la mossa all'array
                moves_array_dict.append(move_dict)

        return moves_array_dict  # restituisco l'array di dizionari

    def __close(self):
        try:
            self.db_file.close()
        except Exception as e:
            pass
            # 23<a3print("ERROR:" + str(e))


if __name__ == '__main__':
    dbca = DBChessAnalizer()

    dbca.generate_json('input.pgn', max_matches=10)

