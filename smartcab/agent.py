import random
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator

number_trials = 100
class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env):
        super(LearningAgent, self).__init__(env)     # sets self.env = env, state = None, next_waypoint = None, and a default color
        self.color = 'red'                           # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint

        # TODO: Initialize any additional variables here
        self.actions = self.env.valid_actions
        self.bad_actions = {}
        self.trial = -1 
        self.lights  = ['green','red']
        self.gamma = 0.5
        
        self.Q = {

                  (action, light, waypoint, oncoming, left, right) : 0   \
                  for action   in self.actions                           \
                  for light    in self.lights                            \
                  for waypoint in self.actions                           \
                  for oncoming in self.actions                           \
                  for left     in self.actions                           \
                  for right    in self.actions                           \
        }

    def reset(self, destination=None):
        self.planner.route_to(destination)
        # TODO: Prepare for a new trip; reset any variables here, if required
        

    def update(self, t):
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        inputs = self.env.sense(self)
        deadline = self.env.get_deadline(self)
        wp = self.next_waypoint
        
        # # Update state
        state = (inputs['light'], wp, inputs['oncoming'], inputs['left'], inputs['right'])
        
        # # Select action according to policy
        current_actions = {action : self.Q[ (action,) + state ] for action in self.actions }
        Q_action = max( current_actions, key=current_actions.get ) # This is the action that has the highest value in Q at the present state 

        action = wp   #reckless   
        #action = self.semi_reckless(Q_action, state)
        #action = Q_action

        # # Execute action and get reward
        reward = self.env.act(self, action)

        # # Learn policy based on state, action, reward
        self.Q[ (action,) + state ] += reward * self.gamma
        
        #print "LearningAgent.update(): deadline = {}, inputs = {}, action = {}, reward = {}".format(deadline, inputs, action, reward)  # [debug]

        # # Tally bad actions
        location = self.env.agent_states[self]['location']
        destination = self.env.agent_states[self]['destination']
        dist = self.env.compute_dist(location, destination)
        
        if t == 0:
            self.trial += 1
            self.bad_actions[self.trial] = 0

        if reward < 0:
            self.bad_actions[self.trial] += 1
            
        if self.trial == number_trials - 1 and (deadline < 1  or dist < 1):
            self.stats()
        # if deadline < 1 or dist < 1:
        #     print "AAAAAH!!! Trial {} BA = {}".format(self.trial, self.bad_actions[self.trial])
        
    def semi_reckless(self, Q_action, state):
        wp = self.next_waypoint
        deadline = self.env.get_deadline(self)
        Q_value  = self.Q[ (Q_action,) + state ]   ## This is how Q rates the above Q_action (the actual max)
        wp_value = self.Q[ (wp,) + state ]         ## This is how Q rates the way_point

        # Making the best choice given our current state
        urgency = 1./(deadline + 0.001)
        two_choices = {Q_action : Q_value * (1 - urgency), wp : wp_value * urgency }

        return max(two_choices, key=two_choices.get)
        
    def stats(self):
        import matplotlib.pyplot as plt
        plt.bar(range(len(self.bad_actions)), self.bad_actions.values(), align='center')
        plt.xticks(range(len(self.bad_actions)), self.bad_actions.keys())
        plt.show()


def run():
    """Run the agent for a finite number of trials."""

    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  # create agent
    e.set_primary_agent(a, enforce_deadline=True)  # specify agent to track
    # NOTE: You can set enforce_deadline=False while debugging to allow longer trials

    # Now simulate it
    sim = Simulator(e, update_delay=0.0, display=False)  # create simulator (uses pygame when display=True, if available)
    # NOTE: To speed up simulation, reduce update_delay and/or set display=False

    sim.run(n_trials=number_trials)  # run for a specified number of trials
    # NOTE: To quit midway, press Esc or close pygame window, or hit Ctrl+C on the command-line


if __name__ == '__main__':
    run()
