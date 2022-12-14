#!/usr/bin/env python3
import socket
import configparser
import time
import os
import pprint
from configparser import ConfigParser

###################
##  MY FUNCTIONS ##
###################

# Checking the ini file and Access the file if no errors
def getGameConfig():
    myc = configparser.ConfigParser()
    try:
        myc.read('./tictac.ini')
        # Checking Headers in the ini file
        myHeaders = myc.sections()
        if 'BASIC' not in myHeaders or 'NETWORKING' not in myHeaders or 'FILTER_SCORE' not in myHeaders:
            #Rasing an Exception
            raise Exception("[Invalid Config Provided] Headers in the Config Not Set Properly")
        else:
            return myc
    except Exception as err:
        # Most probable cause: tictac.ini not provided / accesible
        print(err," Gameconfig not Found / is inaccesible by the Client")
        #Exiting the program
        exit()
        
global_config = getGameConfig()

def gameServerConnect():
    # This function Establishes the connention to server socket of the game
    server_ip = global_config['NETWORKING']['serverIP']
    server_port = int(global_config['NETWORKING']['port'])
    
    connectionTuple = (server_ip,server_port)
    
    clientSocket = socket.socket()
    clientSocket.connect(connectionTuple)

    return clientSocket

def saveGameState(g):
    # This server saves the game to the 'saveDir' Directory that is taken from the config
    saveDir = global_config['BASIC']['saveDir']
    try:
        # Accessing the 'saveDir' Directory and making it if it is not present!
        os.mkdir(saveDir)
    except:
        # This block only executes if the Directory is not present!
        # So we pass the except block
        pass
    # Get Current Time, to append in the filename of the to be saved game
    current_time = time.localtime()

    newSaveFileName = "game-"+current_time
    # Now making the new gameFile
    with open(saveDir + '/' + newSaveFileName, 'w+') as myfile:
        # Writing to the newly created file
        myfile.write(g)
        # Closing the file write stream 
        myfile.close()

def loadGame(load_file_name):
    
    # Getting the 'saveDir' form globalConfig
    saveDir = global_config['BASIC']['saveDir']
    try:
        # Opening the gameLoadFile and reading the data then returning it!
        loadFile = open(saveDir + '/' + load_file_name, 'r')
        data = loadFile.readLine()
        return data
    except:
        # Exception raised only if the load_file_name is not present / is invalid
        raise Exception('Load File Not Present')
    
def gameScoreCard(currentWinner):
    # Getting the current Winner of the game and adding his score
    currentTime = time.localtime()
    # Converting the time to %b $d %Y %H%M form
    currentTime = time.strftime('%b-%d-%Y_%H%M', currentTime)

    scoreDir = global_config['BASIC']['score']

    #Writing the Scores to the score file
    with open(scoreDir, 'at') as f:
        f.write(currentWinner + '   ' + currentTime + '\n')


def gameloop(gameMode, clientSocket):
    print('\n\n')
    # Segregating between the New Game and the Saved Game!
    if gameMode == 'NEW':
        print('New Game started!')
    elif gameMode == 'SAVED':
        print('Continuing a saved game!')
    
    # This Loop runs till the game is being played
    # This loop is responsible for taking in-game inputs
    # and drawing the gameboard
    # and when game ends this loop prints the results

    while True:
        resp = clientSocket.recv(4096)
        resp: object = resp.decode()

        if "BORD" in resp:
            resp = resp[5:]
            print(resp[0:5])
            print(resp[6:11])
            print(resp[12:17])
        
        if 'EROR' in resp:
            print('INVALID MOVE, Retry. Move Syntax -> MOVE:X,Y | Eg. -> MOVE:1,1')
        
        if 'OVER' in resp:
            resp = resp[5:]
            winner = resp[:1]
            print(resp)
            print('*-_-*-_-*-_-* GAME OVER *-_-*-_-*-_-* ')
            gameResult = ''
            if winner == 'N':
                gameResult = 'Tie\n*All good in the end* '
            elif winner == 'S':
                gameResult = 'Server\nSorry! You lost.'
            else:
                gameResult = 'Client\n You Won! Yay!'
            
            print('GAME RESULT : '+gameResult)


            gameScoreCard(winner)
            print(resp[2:7])
            print(resp[8:13])
            print(resp[14:19])
            print()
            
            willPlayAgain = input('Another Game? [Y/N]').upper()
            if willPlayAgain == 'Y':
                clientSocket.send('NEWG'.encode())
                continue
            else:
                break

        move = input("Make Your Move-> ")

        if move == 'ENDG':

            # Sending the Command ENDG to the server to indicate the game has Ended 
            # And is ready to be Saved

            clientSocket.send(move.encode())
            response = clientSocket.recv(4096)
            response = response.decode('utf-8')
            game_state = response[7:]

            saveGameState('X,' + game_state)
            print()
            print("THE GAME HAS BEEN SAVED")
            print()
            break

        clientSocket.send(move.encode())


def drawMenu():
    # This function not only draws the game menu but also is responisble for the navigation between the menu options!
    # Drawing the Game Menu
    global global_config
    menu_str = """-*-_-*-_-*-_-*-_-*- TIC-TAC-TOE -*-_-*-_-*-_-*-_-*-_-*-\n\n---MENU---\n---Choose From The Options Below\n---\tNew Game---->NEWG\n---\tLoad Game---->LOAD\n---\tScore---->SCOR\n---\tConfig---->CONFIG\n---\tExit---->CLOS\n"""
    myConnection = gameServerConnect()
    options = ['NEWG','LOAD','SCOR','CONFIG','CLOS']
    while True:
        print(menu_str)
        choice = input("\t::")
        if choice not in options:
            print("---WRONG CHOICE. Please input a valid choice")
        
        if choice == 'NEWG':
            myConnection.send(choice.encode())
            gameloop('NEW', myConnection)

        if choice == 'LOAD':
            saveDir = global_config['BASIC']['saveDir']
            print("\nSelect a file to load game from\n")
            try:
                print(os.listdir(saveDir))
            except:
                print("\n**No saved file to load!**\n")
                continue
            print()
            fileToLoad = input('SELECT FILE: ')
            try:
                loadState = loadGame(fileToLoad)
                query = 'LOAD:'+loadState

                myConnection.send(query.encode())
                gameloop('SAVED', myConnection)
            except:
                print('The File Failed to Load!')
        
        if choice == 'SCOR':
            scoreDir = global_config['BASIC']['score']
            with open(scoreDir,'r') as scoreFile:
                for line in scoreFile:
                    print(line)
        
        if choice == 'CONFIG':
            global_config = getGameConfig()
            pprint.pprint({section: dict(global_config[section]) for section in global_config.sections()})

        if choice == 'CLOS':
            print('*-_-*-_-*-_-*-_-*-_-*-_-*-_-*-_-')
            print('*-_-*-_-*- GOODBYE -*-_-*-_-*-_-')
            print('*-_-*-_-*-_-*-_-*-_-*-_-*-_-*-_-')

            exit()

start = drawMenu()