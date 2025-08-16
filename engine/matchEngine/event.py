""""""
"""event occured overwrites and changes states regardless of ball_status
has the role of being the refarees whistle to send us to the next state

try_given penalty_given fk_given, scrum_given, penalty_try_given, 
Ball determines lineout already, ball_dead , grounded_in_goal , held_up

penalty_given is a shell that then runs set_piece choices and receives there pick of what to do that will change the next state,
either something for nudeges or scrum

event.py
should have the following 
for each event if statements that determine when they are called 

then a controller function that checks if these have happened and update state.status  
to note this is onl for events but noth state.status and ball.status will influence state.status if they themselves have a new action






"""
