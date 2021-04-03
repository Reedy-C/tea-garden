#Garden

Garden is a research-focused artificial life simulator, designed and created by Cara Reedy for their undergraduate research and then further developed and used for their Ph.D thesis work. It is a multi-agent simulation where each agent has evolving neural networks.

#Running Garden

Garden requires PyCaffe, Pygame, and the separate DGEANN module, which runs the neural networks.

The main file is garden\_experiment.py. While the program can be used by manually setting parameters with the run\_experiment() function, it is easier to set them with a text file (described below) and use run\_from\_file(f), which is run automatically (using the file name 'run params example.txt') when garden\_experiment.py is run. Note: it may take a few seconds for the program to start up.

Garden can be run with or without visualization; it is off by default. The agents are always trying to perform some action, even if it looks like they are sitting there when visualization is turned on. In visual mode, the simulation runs at 10 ticks/second, but this can be changed by changing the number in 'self.clock.tick(10)' in the MainLoop function of garden_experiment.py, or turned off to run as fast as possible by commenting out that line.

During each time step, the creatures are given an array of twelve numbers as input. The first six numbers represent what the creature sees. The creatures can only see what is directly in front of them, and they are told by the simulation exactly what kind of object they are looking at. Each type of object corresponds to a position in the array - this is what the 'node' property of each Widget sub-class refers to. For example, the Dirt objects, which have node set to 0, correspond to the first space of the input array.

The next four numbers are the creature's drives. In order, they are fullness, amusement, pain, and desire, and the first three decrease over time. If a creature's fullness reaches 0, it will starve to death. This happens in 300 ticks. Accumulated pain acts like stress, shortening an agent's life; retaining a high level of amusement moderates this effect and can help the agent live a bit longer. Desire rises and falls on its own, with a period of 1004 ticks; agents are only able to mate when it is in a certain ranger, and mating attempts will lower it, though failed ones by a lesser amount. The drives can also changed by interaction with the objects; for example, attempting to eat a rock increases pain.

The last two numbers are only used if an agent is looking at another agent. The first number indicates if the other agent is currently able to mate. The second is only used if family detection is on, indicating relatedness to the other agent, or if phenotype preferences are on, indicated how similar their phenotypes are.

The creature also takes its last action as input to its 'STM' (short-term memory) layer. As a creature repeats an action, that node in the STM layer gains a higher value. When the creature does a different action, the node decays towards zero.

The output of the creature's neural network is an array of six numbers. The member of the array that is highest is taken as the creature's action. The corresponding list of actions can be seen at the bottom of garden.py. For example, if the output is [3.456, -1.135, 1.789, 0.597, 4.015], then the fifth action will be used, which is 'attempt to play with whatever is in front of me'. Each object defines the outcome of that action on the creature's drives.

The neural network of a creature is defined by its genome. This is by default diploid, with either identical or different starting chromosomes, but can also be haploid. By default, starting chromosomes are drawn from the 'Default Genetics' folder to make populations more successful, but random starting genetics can be used if desired. Agents are able to mate with recombination and make further agents, which may have mutations from their parents. Agent information such as generation number or age at death can be exported to a csv data file; full genomes can also be exported to a csv file listing all genes. These files appear in the 'Data' folder.

Agents have an age-related chance of dying naturally. Higher amounts of accumulated pain will increase the agent's age for the purpose of this calculation, while negative amounts will decrease it. Agents will always die at 130000 time-steps.

#Parameters

The possible parameters for the simulation are (defaults show in parentheses):
x\_loops (1): How many times the simulation will be re-run
max\_ticks (100000): Maximum number of time-steps the simulation will be allowed to run
display\_off (False): If True, no visualization is used (much faster)
garden\_size (13): Sets the size of the simulation area as X by X squares
tako\_number (20): Initial number of agents
pop\_max (25): Maximum population size; at this limit, breeding will no longer produce more agents until some die
max\_width (1800): If display\_off = False, the maximum width in pixels of the visualization window size
max\_height (900): Maximum height in mixes of visualization window size
filename (default file): File name used for collecting data
collect\_data (True): Collects various data about agents and stores it in Data\(filename).csv
export\_all (True): Collects genetic data about agents and stores it in Data\(filename) gene data.csv
rand_nets (False): Initializes agents with random neural networks instead of one of the default networks.
max_gen (5): Maximum generation number allowed; halts the simulation when the first of generation x+1 is born. Will run until infinity or all agents are dead if set <=0.
genetic_mode (Plain): Can be set to Plain (diploid; starts with both chromosomes having identical genes), Diverse (diploid; starts with both chromosomes having different genes), or Haploid. I have found that Plain generally performs best
seeds (None): Set random seeds for the simulation; to list several, use a space between each. If x_loops > 1, they will be used in order
garden\_mode (Diverse Static): Can be set to one of four values - 'Diverse Static' has an unchanging environment with two equally nutritive food types, 'Single Static' only has one food type, 'Nutrition' has both types but which gives more nutrition changes every 40k time-steps, and 'Changing' has only one type present at a given time but which one changes every 100k time-steps
family\_detection (None): Can be set to None (no effect), Degree (agents detect family relationships out to third degree relatives), or Genoverlap (agents detect how much genetic overlap they have with other agents)
family\_mod (0): Can be used to moderate the chance of mating with relatives based on the strength of family relationship, from 0 (no effect) to 1 (strongest restriction)
record_inbreeding (True): If True, records the genetic overlap and degree of relationship between an agent's parents
inbreed\_lim (1.1): If set to between 0 and 1, an agent with that percentage of parental genetic overlap or more will die instantly
hla\_genes (0): If set to > 0, starting agents will be given X random pairs of HLA-inspired health genes, which have 6 alleles. Carrying two of the same allele gives the agent a genetic disorder, cutting its potential life-span by a third
binary\_health (0): If set to > 0, starting agents will be given X random pairs of abstracted Mendelian 'health' genes, where the dominant A is no disorder and the recessive B is a disorder. A disorder cuts the agent's potential life-span by a third
carrier_percentage (40): Int. If binary\_health is > 0, this determines the chance that an initial agent will be made a disorder carrier for each pair of binary health genes
two\_envs (False): If True, creates two different, separated environments
diff\_envs (False): If True and two\_envs is True, gives one environment only one food source type and the other only the other
migration\_rate (0): Float. If > 0 and two\_envs is True, takes that percentage of each agent population in each environment and moves them to the other environment
phen\_pref (False): If True, initial agents are given a pair of genes seting their phenotype mating preference from -1 (prefers totally different mates) to 1 (prefers mates as similar as possible)

#Other files

garden.py defines the environment of the simulation.
tako.py defines the agents of the Garden environment.
widget.py defines the objects that exist in the Garden environment (the agents are a special type of object).
garden\_task.py defines the processing layer that goes between the simulation, environment, and the neural network of the creatures. It handles the process of the creatures taking input from the environment, deciding what action a creature takes, and sending actions to the environment to be performed.
tako\_genetics.py defines particular DGEANN genetics variations used for agents when some parameters are turned on.
genetics tests.py contains some genetics tests peculiar to this use of DGEANN.
