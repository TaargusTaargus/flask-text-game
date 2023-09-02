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
    response = ''
    user_input = ''
    
    if request.method == 'POST':
        user_input = request.form.get( 'user_input' )
        
        if user_input == "debug":
            response = game.to_json_string()
        else:
            response = game.interact( user_input )

        session[ 'game' ] = game.to_json_string()
        
    return render_template( 'index.html', response = response, user_input = user_input )


@app.route( '/edit/game', methods=['GET', 'POST'] )
def edit_game():
    game = __check_session__()
    
    if request.method == 'POST':
        game.current = request.form.get( 'current' )
        session[ 'game' ] = game.to_json_string()
        return redirect( url_for( 'edit_game' ) )
    
    return render_template( 'edit_game.html', game = game )


@app.route('/new_game')
def new_game():
    session[ 'game' ] = PlayerContext().to_json_string()
    return redirect( url_for( 'edit_game' ) )


@app.route('/reset_game')
def reset_game():
    game = __check_session__( force_reset = True )
    return redirect( url_for( 'index' ) )


@app.route('/context/add', methods=['GET', 'POST'])
def add_context():
    game = __check_session__()
    
    if request.method == 'POST':
        game.possible[ request.form.get( 'key' ) ] = GameContext()
        session[ 'game' ] = game.to_json_string()
        return redirect( url_for( 'edit_game' ) )

    return render_template( 'add_context.html' )


@app.route('/event/delete/<roomid>')
def delete_context( roomid ):
    game = __check_session__()
    game.remove_gamecontext( roomid )
    session[ 'game' ] = game.to_json_string()
    return redirect( url_for( 'edit_game' ) )


@app.route('/context/edit/<roomid>')
def edit_context( roomid ):
    game = __check_session__()
    context = game.possible[ roomid ]
    return render_template( 'edit_context.html', context = context, roomid = roomid )


@app.route('/event/add/<roomid>/<etype>', methods=['GET', 'POST'])
def add_event( roomid, etype ):
    game = __check_session__()
    event_entry = EVENT_FACTORY[ etype ]( {} )
    
    if request.method == 'POST':
        
        form_name = request.form.get( 'form_name' )
        
        if form_name == 'event_type_form':
            return redirect( url_for( 'add_event', roomid = roomid, etype = request.form.get( 'event_type' ) ) )
        else:
            attributes = event_entry.attributes
            for key in attributes:
                if isinstance( attributes[ key ], bool ):
                    attributes[ key ] = request.form.get( key ) == "on"  # Convert checkbox value to boolean
                else:
                    attributes[ key ] = request.form[ key ]

            game.possible[ roomid ].add_event( request.form.get( 'key' ), event_entry )
            session[ 'game' ] = game.to_json_string()
            return redirect( url_for( 'edit_context', roomid = roomid ) )

    return render_template(
        'add_event.html'
        , event = event_entry
        , event_type = etype
        , event_types = EVENT_FACTORY.keys()
    )


@app.route('/event/delete/<roomid>/<eid>')
def delete_event( roomid, eid ):
    game = __check_session__()
    game.possible[ roomid ].remove_event( eid )
    session[ 'game' ] = game.to_json_string()
    return redirect( url_for( 'edit_context', roomid = roomid ) )


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
        return redirect( url_for( 'edit_context', roomid = roomid ) )

    return render_template(
        'edit_event.html'
        , eid = eid
        , event = event_entry[ 'event' ]
        , event_key = event_entry[ 'key' ]
        , event_type = event_entry[ 'type' ]
        , roomid = roomid
    )



if __name__ == '__main__':
    app.run( debug=True, use_reloader=False )
