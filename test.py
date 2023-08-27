from game import GameContext, PlayerContext, TextEvent, MoveEvent, UpdateEvent

def test_game():
    gc1 = GameContext()
    gc1.add_event( "hello", TextEvent( "Hello!" ) )
    gc1.add_event( "goodbye", TextEvent( "Goodbye!" ) )
    gc1.add_event( "french", MoveEvent( 'two' ) )


    gc2 = GameContext()
    gc2.add_event( "bonjour", TextEvent( "Bonjour!" ) )
    gc2.add_event( "aurevoir", TextEvent( "Au revoir!" ) )
    gc2.add_event( "english", MoveEvent( 'one' ) )

    eid = gc2.add_event( "drink", TextEvent( "You drink the wine.", enable = False, persist = False ) )
    gc1.add_event( "wine", UpdateEvent( "You pick up the wine.", "two", eid, { 'enable': True } ) )



    
    pc = PlayerContext()
    pc.current = 'one'
    pc.possible = {
        'one': gc1
        , 'two': gc2
    }
    return pc

def test_command_line():
    pc = test_game()

    # tries writing and reading from a json string
    tmp = pc.to_json_string()
    pc = PlayerContext.from_json_string( pc, tmp )

    ## game
    uinput = None

    while uinput != "exit":

        uinput = input( "----> " )

        if uinput != 'exit':
            print( pc.interact( uinput ) )


#test_command_line()
