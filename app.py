from datetime import timedelta
from flask import Flask, redirect, render_template, request, Response, session, url_for
from game import EVENT_FACTORY, GameContext, PlayerContext
from test import test_game

app = Flask( __name__ )
app.secret_key = 'your_secret_key'  # Change this to a secure secret key
app.config[ 'PERMANENT_SESSION_LIFETIME' ] = timedelta( minutes = 30 )  # Adjust session timeout as needed

## intializes the user session
def __check_session__( force_reset = False ):
    
    if 'game' not in session or force_reset:
        session[ 'game' ] = test_game().to_json_string()
        
    return PlayerContext.from_json_string( PlayerContext(), session[ 'game' ] )


@app.route('/download_game')
def download_json():
    game = __check_session__()
    
    # Create a response with the JSON data
    response = Response( game.to_json_string(), content_type='application/json' )
    
    # Set the content-disposition header to trigger download
    response.headers[ "Content-Disposition" ] = "attachment; filename=data.json"
    
    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    game = __check_session__()
    
    user_input = ''
    response = ''
        
    if request.method == 'POST':
        
        user_input = request.form.get('user_input')

        if user_input == "debug":
            response = game.to_json_string()
        else:
            response = game.interact( user_input )

        session[ 'game' ] = game.to_json_string()
        
    return render_template( 'index.html', user_input = user_input, response = response )


@app.route('/game')
def game():
    game = __check_session__()
    return render_template( 'game.html', game = game )


@app.route('/context/<roomid>')
def context( roomid ):
    game = __check_session__()
    context = game.possible[ roomid ]
    return render_template( 'context.html', context = context, roomid = roomid )


@app.route('/context/add', methods=['GET', 'POST'])
def add_context():
    game = __check_session__()
    
    if request.method == 'POST':
        game.possible[ request.form.get( 'key' ) ] = GameContext()
        session[ 'game' ] = game.to_json_string()
        return redirect( url_for( 'game' ) )

    return render_template( 'add_context.html' )


@app.route('/event/add/<roomid>', methods=['GET', 'POST'])
def add_event( roomid ):
    game = __check_session__()
    event_entry = EVENT_FACTORY[ 'text' ]( {} )
    
    if request.method == 'POST':

        attributes = event_entry.attributes
        for key in attributes:
            if isinstance( attributes[ key ], bool ):
                attributes[ key ] = request.form.get( key ) == "on"  # Convert checkbox value to boolean
            else:
                attributes[ key ] = request.form[ key ]

        game.possible[ roomid ].add_event( request.form.get( 'key' ), event_entry )
        session[ 'game' ] = game.to_json_string()
        return redirect( url_for( 'context', roomid = roomid ) )

    return render_template( 'add_event.html', data_dict = event_entry )


@app.route('/event/edit/<roomid>/<eid>', methods=['GET', 'POST'])
def edit_event( roomid, eid ):
    game = __check_session__()
    event_entry = game.possible[ roomid ].events[ eid ]
    
    if request.method == 'POST':

        attributes = event_entry[ 'event' ].attributes
        for key in attributes:
            if isinstance( attributes[ key ], bool ):
                attributes[ key ] = request.form.get( key ) == "on"  # Convert checkbox value to boolean
            else:
                attributes[ key ] = request.form[ key ]
                
        event_entry[ 'key' ] = request.form.get( 'key' )
        session[ 'game' ] = game.to_json_string()
        return redirect( url_for( 'context', roomid = roomid ) )

    return render_template( 'edit_event.html', data_dict = event_entry )


if __name__ == '__main__':
    app.run( debug=True, use_reloader=False )
