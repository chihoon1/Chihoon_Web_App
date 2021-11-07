import sqlite3


def create_gomoku_table(db_name='db.sqlite3'):
    conn = sqlite3.connect(db_name)
    conn.execute("CREATE TABLE gomoku_gomoku ( rowid INTEGER, \
                        grid Text, \
                        number_turns TEXT, \
                        whose_turn TEXT, \
                        difficulty_level TEXT, \
                        player1_name TEXT, \
                        player1_color TEXT, \
                        player2_name TEXT, \
                        player2_color TEXT);")
    conn.commit()
    conn.close()


if __name__ == '__main__':
    create_gomoku_table('gomoku_db.sqlite3')  # this will create a database in gomoku app folder