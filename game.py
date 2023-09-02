import json
import time

EVENT_FACTORY = {
    "move": lambda args : MoveEvent( **args )
    , "narrative": lambda args : NarrativeEvent( **args )
    , "text" : lambda args : TextEvent( **args )
    , "update": lambda args : UpdateEvent( **args )
}

## actions
class Event:
    def __init__(self, attributes, enable = True, persist = True):
        self.attributes = attributes
        self.attributes[ 'enable' ] = enable
        self.attributes[ 'persist' ] = persist

    def fire(self, context):
        raise NotImplementedError("Subclasses must implement the 'fire' method.")

    def persist(self):
        return self.attributes[ 'persist' ]

    def enable(self):
        return self.attributes[ 'enable' ]

    def type(self):
        raise NotImplementedError("Subclasses must implement the 'type' method.")

    def to_json_string( self ):
        return json.dumps(self.attributes,indent=4)

    def from_json_string(self, json_string):
        self.attributes = json.loads(json_string)

    def to_json_serializable( self ):
        return self.attributes
        

## primitive event, returns a text
class NarrativeEvent(Event):
    def __init__(self, return_text = "", enable = True, persist = True):
        super().__init__( {"return_text": return_text}, enable, persist )
        
    def fire(self, context):
        context.narrative = self.attributes[ 'return_text' ]
        return None

    def type(self):
        return "narrative"



## update event attributes
class UpdateEvent(Event):
    def __init__(self, return_text = "", gc_id = "", event_id = "", nattributes = "", enable = True, persist = False):
        super().__init__( {"return_text": return_text, "gc_id": gc_id, "event_id": event_id, "nattributes": nattributes}, enable, persist )
        
    def fire(self, context):
        event = context.possible[ self.attributes[ 'gc_id' ] ].events[ self.attributes[ 'event_id' ] ][ 'event' ]
        for key in self.attributes[ 'nattributes' ]:
            event.attributes[ key ] = self.attributes[ 'nattributes' ][ key ]

        return self.attributes[ 'return_text' ]

    def type(self):
        return "update"


## primitive event, returns a text
class TextEvent(Event):
    def __init__(self, return_text = "", enable = True, persist = True):
        super().__init__( {"return_text": return_text}, enable, persist )

    def fire(self, context):
        return self.attributes[ 'return_text' ]

    def type(self):
        return "text"



## primitive event, changed context
class MoveEvent(Event):
    def __init__(self, next_context = "", enable = True, persist = True):
        super().__init__( {"next_context": next_context}, enable, persist )

    def fire(self, context):
        context.current = self.attributes[ 'next_context' ]
        return f'Moved to {self.attributes["next_context"]}.'


    def type(self):
        return "move"


## world
class GameContext:
    
    def __init__(self):
        self.events = {}

    def add_event(self, event_name, event ):
        eid = str( len( self.events ) )
        self.events[ eid ] = {
            "type": event.type()
            , "key": event_name
            , "event": event
        }
        return eid


    def remove_event(self, event_id):
        del self.events[ event_id ]

    def to_json_string(self):
        data = { "events": {} }
        for e in self.events:
    
            data[ "events" ][ e ] = {
                    'type': self.events[ e ][ 'type' ]
                    , 'key': self.events[ e ][ 'key' ]
                    , 'event': self.events[ e ][ 'event' ].to_json_serializable()
            }

        return json.dumps(data,indent=4)


    def from_json_string(cls,json_string):
        data = json.loads(json_string)
        tmp = data.get("events", {})
        
        for e in tmp:
            
            cls.events[ e ] = []
            args = tmp[ e ][ 'event' ]
            cls.events[ e ] =  {
                'type': tmp[ e ][ 'type' ]
                , 'key': tmp[ e ][ 'key' ]
                , 'event': EVENT_FACTORY[ tmp[ e ][ 'type' ] ]( args )
            } 
                
        return cls

    def to_json_serializable(self):
        data = { "events": {} }
        for e in self.events:
    
            data[ "events" ][ e ] = {
                    'type': self.events[ e ][ 'type' ]
                    , 'key': self.events[ e ][ 'key' ]
                    , 'event': self.events[ e ][ 'event' ].to_json_serializable()
            }

        return data
    


## point of view
class PlayerContext:

    def __init__(self):
        self.current = None
        self.narrative = None
        self.possible = {}


    def interact(self, event_name):
        
        current = self.possible[ self.current ]
        events = []
        for e in current.events:
            if current.events[ e ][ 'key' ] == event_name and current.events[ e ][ 'event' ].enable():
                events.append( ( e, current.events[ e ][ 'event' ] ) )

        if len( events ):

            ret  = ""
            for eid, event in events:

                eret = event.fire( self )

                if eret: 
                    ret = ret + eret + "\n"

                if not event.persist():
                    current.remove_event( eid )
            
            return ret.strip()
        
        else:
            
            return f"Try one of these inputs: {', '.join( [ current.events[ event ][ 'key' ] for event in current.events if current.events[ event ][ 'event' ].enable() ] )}"


    def add_gamecontext(self, context_name, context ):
        self.possible[ context_name ] = context
        return context_name


    def remove_gamecontext(self, gc_id):
        del self.possible[ gc_id ]
        

    def to_json_string(self):
        data = {
            "current": self.current,
            "narrative": self.narrative,
            "possible": { e : self.possible[ e ].to_json_serializable() for e in self.possible }
        }
        return json.dumps(data, indent=4)


    def from_json_string( cls, json_string ):
        data = json.loads( json_string)
        cls.current = data.get( "current")
        cls.narrative = data.get( "narrative" )
        possible = data.get( "possible", {} )
        for eid, value in possible.items():
            cls.possible[ eid ] = GameContext.from_json_string( GameContext(), json.dumps( value ) )
        return cls



