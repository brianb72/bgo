# BGO

Database and search engine for the game of Go that allows positional searches on a collection of game records

This is a rough draft exploring what can be done with a command line Go database.

**What is Go?**

Go is a two player asian board game played on a board of 19 by 19 lines. One player uses black stones, the other uses 
white. Players take turns placing a single stone on the board at a time. Stones do not move once placed. The goal of 
the game is to surround an many empty intersections (territory) as possible.

Learn Go:
https://www.usgo.org/learn-play 

**Features**

* BGO Library for database access, go board with rules of go, game record parser, coordinate conversion, diagram generator.
* BSHELL command line interface for selecting database, importing games, rebuilding hashes, and performing simple searches on a text based board.
* REPORTS generator to search the database and generate HTML reports

**Code Use**
   
* Prompt-Toolkit command line interface https://github.com/mpirnat/dndme
* JGO javascript board https://github.com/jokkebk/jgoboard
* Game of Go implementation https://github.com/brilee/go_implementation/blob/master/go_naive.py

**How to use**

From the root directory of the project:
   
    python -m bshell.bshell
    python -m reports.openingbook
    
**Project Layout**
* bgo
    * bgo
        * coords.py - Conversion between different coordinate types, handles board rotation and mirroring
        * db_access.py - Access to SQLite database
        * diagrams.py - Helper class to generate board diagrams used by JGO
        * game_of_go.py - Place stones on a go board, handle captures and ko
        * go_board.py - Wrapper for game_of_go, will eventually replace game_of_go completely
        * preferred_rotation.py - Uses simple preference rules to find the best rotation for a board
        * sgf_parser - Uses SmartGo SGF parser to read a game record, extract and decode fields
    * bshell
        * bshell.py - Command line interface to access the database
        * models.py - Objects used by bshell
        * commands - All commands used by bshell
    * report
        * openingbook.py - Produces a multipage HTML document showing most the most popular first 4 moves and variations for moves 5-7
    * HTML - Output directory for report generator
    * baduk.sqlite - Default database
    * TestSGF.tgz - A small collection of game records that can be imported into the database
    
   
    
**Example shell usage:**

    [brian@kmhvn bgo]$ python -m bshell.bshell
    Start /home/brian/Projects/git/bgo/bshell  Work /home/brian/Projects/git/bgo
    Using database [/home/brian/Projects/git/bgo/baduk.sqlite] with 101341 games.
    Registered Board
    Registered Buildhash
    Registered Cd
    Registered Cwd
    Registered Dbfile
    Registered Help
    Registered Import
    Registered ListCommands
    Registered Ls
    Registered Mark
    Registered Play
    Registered Search
    Registered Undo
    
    > dbfile test.sql                                                                                                   
    
    *** Database /home/brian/Projects/git/bgo/test.sql does not exist.
       Create new database? (YES) > YES                                                                                 
       Opened /home/brian/Projects/git/bgo/test.sql with 0 games.

    > cd /home/brian/Data/Go/SGF                                                                                        
    Working directory changed to /home/brian/Data/Go/SGF
    
    > ls                                                                                                                
    Directory: /home/brian/Data/Go/SGF
       Directories: [GoKifu], [BadukMovies], [GoGod]
             Files: BadukMovies.tgz, GoKifu.tgz, test.sql, GoGod.tgz
    
    > import GoGod.tgz                                                                                                  
    
    *** About to import /home/brian/Data/Go/SGF/GoGod.tgz
       Are you sure? (YES) > YES                                                                                        
    Begining import...
    60608 files in archive. 0:00:04.585806
       1000 / 60608 ( 1.65%) [0:00:26.911115]
       2000 / 60608 ( 3.30%) [0:00:25.520097]
       3000 / 60608 ( 4.95%) [0:00:25.219960]
       ... snip ...
       58000 / 60608 (95.70%) [0:00:25.357722]
       59000 / 60608 (97.35%) [0:00:20.337879]
       60000 / 60608 (99.00%) [0:00:25.281385]
    Elapsed Time: 0:24:04.147548
    Found 60350 game records, added 56670 games.
    1 duplicates, 3679 parse errors
  
    > buildhash                                                                                                         
    
    *** Really erase and rebuild all hashes? This will take some time.
       Are you sure? (YES) > YES                                                                                        
       1000 / 56670 ( 1.76%) [29970 hashes buffered] [0:00:01.940636]
       2000 / 56670 ( 3.53%) [59970 hashes buffered] [0:00:01.940544]
       3000 / 56670 ( 5.29%) [89970 hashes buffered] [0:00:01.935929]
        ...snip...
       14000 / 56670 (24.70%) [419951 hashes buffered] [0:00:01.931410]
       15000 / 56670 (26.47%) [449951 hashes buffered] [0:00:01.933159]
       16000 / 56670 (28.23%) [479951 hashes buffered] [0:00:01.932707]
       ...Inserting 500021 hashes into the database.
       ...Finished in 0:00:02.668882
       17000 / 56670 (30.00%) [9930 hashes buffered] [0:00:04.600056]
       18000 / 56670 (31.76%) [39930 hashes buffered] [0:00:01.928491]
       19000 / 56670 (33.53%) [69930 hashes buffered] [0:00:01.931112]
        ...snip...
       54000 / 56670 (95.29%) [119815 hashes buffered] [0:00:01.933220]
       55000 / 56670 (97.05%) [149815 hashes buffered] [0:00:01.931756]
       56000 / 56670 (98.82%) [179815 hashes buffered] [0:00:01.927817]
    Elapsed: 0:02:02.177548
    56670 games processed, 0 games with illegal moves.
    
    > board                                                                                                             
    
       A B C D E F G H I J K L M N O P Q R S
     a . . . . . . . . . . . . . . . . . . . a
     b . . . . . . . . . . . . . . . . . . . b
     c . . . . . . . . . . . . . . . . . . . c
     d . . . + . . . . . + . . . . . + . . . d
     e . . . . . . . . . . . . . . . . . . . e
     f . . . . . . . . . . . . . . . . . . . f
     g . . . . . . . . . . . . . . . . . . . g
     h . . . . . . . . . . . . . . . . . . . h
     i . . . . . . . . . . . . . . . . . . . i
     j . . . + . . . . . + . . . . . + . . . j
     k . . . . . . . . . . . . . . . . . . . k
     l . . . . . . . . . . . . . . . . . . . l
     m . . . . . . . . . . . . . . . . . . . m
     n . . . . . . . . . . . . . . . . . . . n
     o . . . . . . . . . . . . . . . . . . . o
     p . . . + . . . . . + . . . . . + . . . p
     q . . . . . . . . . . . . . . . . . . . q
     r . . . . . . . . . . . . . . . . . . . r
     s . . . . . . . . . . . . . . . . . . . s
       A B C D E F G H I J K L M N O P Q R S
       
    > play pd dp qp dd fq cn                                                                                            

       A B C D E F G H I J K L M N O P Q R S
     a . . . . . . . . . . . . . . . . . . . a
     b . . . . . . . . . . . . . . . . . . . b
     c . . . . . . . . . . . . . . . . . . . c
     d . . . O . . . . . + . . . . . X . . . d
     e . . . . . . . . . . . . . . . . . . . e
     f . . . . . . . . . . . . . . . . . . . f
     g . . . . . . . . . . . . . . . . . . . g
     h . . . . . . . . . . . . . . . . . . . h
     i . . . . . . . . . . . . . . . . . . . i
     j . . . + . . . . . + . . . . . + . . . j
     k . . . . . . . . . . . . . . . . . . . k
     l . . . . . . . . . . . . . . . . . . . l
     m . . . . . . . . . . . . . . . . . . . m
     n . . O . . . . . . . . . . . . . . . . n
     o . . . . . . . . . . . . . . . . . . . o
     p . . . O . . . . . + . . . . . + X . . p
     q . . . . . X . . . . . . . . . . . . . q
     r . . . . . . . . . . . . . . . . . . . r
     s . . . . . . . . . . . . . . . . . . . s
       A B C D E F G H I J K L M N O P Q R S
       
    > search                                                                                                            

       A B C D E F G H I J K L M N O P Q R S
     a . . . . . . . . . . . . . . . . . . . a
     b . . . . . . . . . . . . . . . . . . . b
     c . . . . . . . . . . . . . . . . . . . c
     d . . . O . . . . . + . . . . . X . . . d
     e . . . . . . . . . . . . . . . . . . . e
     f . . . . . . . . . . . . . . . . . . . f
     g . . . . . . . . . . . . . . . . . . . g
     h . . . . . . . . . . . . . . . . . . . h
     i . . . . . . . . . . . . . . . . . . . i
     j . . . + . . . . . + . . . . . + . . . j
     k . . . . . . . . . . . . . . . . . . . k
     l . . . . . . . . . . . . . . . . . . . l
     m . . . . . . . . . . . . . . . . . . . m
     n . . O . . . . . . . . . . . . . . . . n
     o . . . . . . . . . . . . . . . . . . . o
     p . . . O . . . . . + f . . . d + X . . p
     q . . . . . X . . . . a b . e . . . . . q
     r . . . c . . . . . . . . . . . . . . . r
     s . . . . . . . . . . . . . . . . . . . s
       A B C D E F G H I J K L M N O P Q R S
    a: 892, b: 765, c: 188, d: 86, e: 66, f: 42
    
    > play a                                                                                                            
    
       A B C D E F G H I J K L M N O P Q R S
     a . . . . . . . . . . . . . . . . . . . a
     b . . . . . . . . . . . . . . . . . . . b
     c . . . . . . . . . . . . . . . . . . . c
     d . . . O . . . . . + . . . . . X . . . d
     e . . . . . . . . . . . . . . . . . . . e
     f . . . . . . . . . . . . . . . . . . . f
     g . . . . . . . . . . . . . . . . . . . g
     h . . . . . . . . . . . . . . . . . . . h
     i . . . . . . . . . . . . . . . . . . . i
     j . . . + . . . . . + . . . . . + . . . j
     k . . . . . . . . . . . . . . . . . . . k
     l . . . . . . . . . . . . . . . . . . . l
     m . . . . . . . . . . . . . . . . . . . m
     n . . O . . . . . . . . . . . . . . . . n
     o . . . . . . . . . . . . . . . . . . . o
     p . . . O . . . . . + . . . . . + X . . p
     q . . . . . X . . . . X . . . . . . . . q
     r . . . . . . . . . . . . . . . . . . . r
     s . . . . . . . . . . . . . . . . . . . s
       A B C D E F G H I J K L M N O P Q R S
       
    > search                                                                                                            

       A B C D E F G H I J K L M N O P Q R S
     a . . . . . . . . . . . . . . . . . . . a
     b . . . . . . . . . . . . . . . . . . . b
     c . . . . . . . . . . . . . d . . . . . c
     d . . . O . . . . . + . . . . . X . . . d
     e . . . . . . . . . . . . . . . . . . . e
     f . . . . . . . . . . . . . . . . b . . f
     g . . . . . . . . . . . . . . . . . . . g
     h . . . . . . . . . . . . . . . . . . . h
     i . . . . . . . . . . . . . . . . c . . i
     j . . . + . . . . . + . . . . . e a . . j
     k . . . . . . . . . . . . . . . . . . . k
     l . . . . . . . . . . . . . . . . . . . l
     m . . . . . . . . . . . . . . . . . . . m
     n . . O . . . . . . . . . . . . f . . . n
     o . . . . . . . . . . . . . . . . . . . o
     p . . . O . . . . . + . . . . . + X . . p
     q . . . . . X . . . . X . . . . . . . . q
     r . . . . . . . . . . . . . . . . . . . r
     s . . . . . . . . . . . . . . . . . . . s
       A B C D E F G H I J K L M N O P Q R S
    a: 771, b: 73, c: 17, d: 8, e: 8, f: 4

    > play b                                                                                                            

       A B C D E F G H I J K L M N O P Q R S
     a . . . . . . . . . . . . . . . . . . . a
     b . . . . . . . . . . . . . . . . . . . b
     c . . . . . . . . . . . . . . . . . . . c
     d . . . O . . . . . + . . . . . X . . . d
     e . . . . . . . . . . . . . . . . . . . e
     f . . . . . . . . . . . . . . . . O . . f
     g . . . . . . . . . . . . . . . . . . . g
     h . . . . . . . . . . . . . . . . . . . h
     i . . . . . . . . . . . . . . . . . . . i
     j . . . + . . . . . + . . . . . + . . . j
     k . . . . . . . . . . . . . . . . . . . k
     l . . . . . . . . . . . . . . . . . . . l
     m . . . . . . . . . . . . . . . . . . . m
     n . . O . . . . . . . . . . . . . . . . n
     o . . . . . . . . . . . . . . . . . . . o
     p . . . O . . . . . + . . . . . + X . . p
     q . . . . . X . . . . X . . . . . . . . q
     r . . . . . . . . . . . . . . . . . . . r
     s . . . . . . . . . . . . . . . . . . . s
       A B C D E F G H I J K L M N O P Q R S

    > search                                                                                                            

       A B C D E F G H I J K L M N O P Q R S
     a . . . . . . . . . . . . . . . . . . . a
     b . . . . . . . . . . . . . . . . . . . b
     c . . . . . . . . . . . . . e . . . . . c
     d . . . O . . . . . + . . . . . X . . . d
     e . . . . . . . . . . . . . . . . . . . e
     f . . . . . . . . . . . . . . . . O . . f
     g . . . . . . . . . . . . . . . . . . . g
     h . . . . . . . . . . . . . . . f c . . h
     i . . . . . . . . . . . . . . . a b . . i
     j . . . + . . . . . + . . . . . d . . . j
     k . . . . . . . . . . . . . . . . . . . k
     l . . . . . . . . . . . . . . . . . . . l
     m . . . . . . . . . . . . . . . . . . . m
     n . . O . . . . . . . . . . . . . . . . n
     o . . . . . . . . . . . . . . . . . . . o
     p . . . O . . . . . + . . . . . + X . . p
     q . . . . . X . . . . X . . . . . . . . q
     r . . . . . . . . . . . . . . . . . . . r
     s . . . . . . . . . . . . . . . . . . . s
       A B C D E F G H I J K L M N O P Q R S
    a: 31, b: 17, c: 16, d: 4, e: 2, f: 2

    > exit                    