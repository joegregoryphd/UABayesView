import json
import os
import pyAgrum as gum
import pyAgrum.lib.image as img
import matplotlib
matplotlib.use('Agg') #Without this matplotlib will throw some errors on frontend


#This cell filters the file to only the relevant lines
def build_relationship_dict(file):
    open_bracket = False #A boolean to check if the bracket is open or not since each relevant structure starts with an open bracket
    relationship = {} #A dictionary to store the relationships that are present in the OML
    info = "" #initializing the info string
    for line in file:
        if line.strip().startswith("ri") or line.strip().startswith("ci"): #Need to strip since there are tabs in the file
            dict_key = line.strip().split(" : ")[0][3:]#Dictionary key
            open_bracket = True #This is to indicate that the bracket is open
        elif line.strip().startswith("ref ci"):
            dict_key = line.strip()
            open_bracket = True #This is to indicate that the bracket is open
        
        if open_bracket: #This should pull the relevant lines from the file
            info += line.strip() + "\n"
            if line.strip().startswith("]"):
                open_bracket = False
                #at this point we have found a full relationship so lets add it to dict
                relationship[dict_key] = info
                info = "" #resetting the info string for the next relationship
                
    return relationship #returning the relationship dictionary


def get_nodes_and_edges(relationship_dict):
    nodes = []
    edges = {}  # The key is the "from" node, and the value is a list of "to" nodes
    parent_child_dict = {} # The key is the "to"(child) node, and the value is a list of "from" (parent) nodes
    parent_child_weight_list = [] # A list of tuples where the first element is the parent and the second element is the child

    for key in relationship_dict.keys():
        node1 = None
        node2 = None
        weight = None
        if relationship_dict[key].startswith("ri"):
            for line in relationship_dict[key].split("\n"):
                if line.startswith("from c"):
                    node1 = line.split(":")[-1].strip()
                elif line.startswith("from"):
                    node1 = line.split()[-1].strip()
                elif line.startswith("to"):
                    node2 = line.split(":")[-1].strip()
                elif line.startswith("bn:hasBayesianWeight"):
                    weight = float(line.split()[-1].strip())
                
            if node1 and node2 and weight is not None:
                parent_child_weight_list.append([node1, node2, weight])

            # Build up edge dict
            if node1 not in edges:
                edges[node1] = []
            edges[node1].append(node2 if 'node2' in locals() else None)

            # Add nodes to list if they are not already in it
            if node1 not in nodes:
                nodes.append(node1)
            if node2 not in nodes and node2 is not None:
                nodes.append(node2)

        elif relationship_dict[key].startswith("ci"):
            node1 = key

            # Add nodes to list if they are not already in it
            if node1 not in nodes:
                nodes.append(node1)
                
   # Build up parent_child_dict by iterating through edges
    for parent, children in edges.items():
        for child in children:
            if child not in parent_child_dict:
                parent_child_dict[child] = []
            parent_child_dict[child].append(parent)

    # Ensure all nodes are present in parent_child_dict
    for node in nodes:
        if node not in parent_child_dict:
            parent_child_dict[node] = None

    return nodes, edges, parent_child_dict, parent_child_weight_list


#This is a helper finction that will be used to help create the conditional probability tables
def decimal_to_binary(decimal_number, num_edges):
    binary_list = [int(x) for x in bin(decimal_number)[2:]]  # Convert decimal_number to binary and remove '0b' prefix
    binary_list = [0] * (num_edges - len(binary_list)) + binary_list  # Pad with zeros to match num_edges
    return binary_list


def bayesian_weight_calculator(cpt_dict, parent_child_weight_list, target_node):
    bay_true = 0
    equation_1 = True #we only have 2 equations so we can use a boolean to switch between them
    for key in cpt_dict.keys():
        if "Error" in key: #a loop to see which equation we will be using
            equation_1 = False
    
    if equation_1: #if its ture we are using the first equation
        weight_binary_list = []
        for key in cpt_dict.keys():
            for entry in parent_child_weight_list:
                if entry[0] ==  key and entry[1] == target_node:
                    weight_binary_list.append([entry[2], cpt_dict[key]]) #This will have a bayesian weight and if its true or false
        for entry in weight_binary_list:
            if entry[1] == 1: #This is true so we do th weight times 1
                bay_true += entry[0] * 1
            else: #This is false so we do the weight times 0
                bay_true += 0

            
    else: #we know we will be using our second equation
        weight_binary_list = []
        weight_error_sum = 0 #initializing the sum of the error weights
        for key in cpt_dict.keys():
            if "Error" not in key and "CalibrationStatus" not in key: #These are both possible sources of error
                passx = key #We know this node will be our passx since its not a source of error
            for entry in parent_child_weight_list:
                if entry[0] == key and entry[1] == target_node:
                    weight_binary_list.append([entry[0], entry[2], cpt_dict[key]]) #This will have a parent name, bayesian weight, if its true or false
        for entry in weight_binary_list:
            if entry[0] == passx:
                if entry[2] == 1: #PassX is true
                    passx_modification = 1
                else: #PassX is false
                    passx_modification = -1
            else: 
                if entry[2] == 0: #This is true so we do th weight times 1
                    weight_error_sum += entry[1] 
                
        bay_true = 0.5 + (0.5* passx_modification) - (passx_modification * weight_error_sum) 
        
    
    return bay_true, 1 - bay_true #returning the probability of the bay_true and bay_false


#This cell will build up the Bayesian Network
def generate_bayes_network(nodes, edges, parent_child_dict, parent_child_weight_list):
    bayes_net = gum.BayesNet("Bayes_Network") #Creating a bayesian network
#This loop will add the nodes to the bayesian network
    bayes_nodes = {} #this will be a dict of all of the nodes converted to the PyAgrum format
    for node in nodes:
        if "Error" in node:
            bayes_nodes[node] = bayes_net.add(gum.LabelizedVariable(node, node, ["Error", "No Error"])) 
        elif "CalibrationStatus" in node:
            bayes_nodes[node] = bayes_net.add(gum.LabelizedVariable(node, node, ["Uncalibrated", "Calibrated"]))
        elif "Accuracy" in node or "Result" in node:
            bayes_nodes[node] = bayes_net.add(gum.LabelizedVariable(node, node, ["Fail", "Pass"]))
        else:
            #The most generic case
            bayes_nodes[node] = bayes_net.add(gum.LabelizedVariable(node, node, ["False", "True"]))
        #FIXME: We are HARD CODING the number of states for now since we know that there are only 2 states for each node
        #FIXME: We need to change this to be more dynamic in the future
            
# This loop will add arcs (fancy name for edges)
    for from_node, to_nodes in edges.items():
        # This is the node that the edge is coming from
        from_node = bayes_nodes[from_node]  # This will get the node from the bayes_nodes dict
        
        # This loop handles cases where there are multiple edges leaving the same node
        for to_node in to_nodes:
            # This is the node that the edge is going to
            to_node = bayes_nodes[to_node]  # This will get the node from the bayes_nodes dict
            
            bayes_net.addArc(from_node, to_node)  # Add directed edges between two nodes (From (Key) -> To (Value))

# This loop will add the CPTs to the Bayesian network
#A CPT for this type of true false would look like this:
#False | False              #0 | 0
#False | True               #0 | 1
#True | False               #1 | 0
#True | True                #1 | 1
#The first column is the parent node and the second column is the child node
#in this code we need a binary truth table where true = 1 and false = 0
#so our table looks like this:  

    cpt_data = []
    for node in nodes: # We will go through each node and generate the CPT for that node
        cpt_entry = { 
            "name": node,
            "parents": parent_child_dict[node] if parent_child_dict[node] else [],
            "states": ["False", "True"],  # Assuming binary states for simplicity
            "probabilities": []
        }#Building up a data structure to hold the CPT data
        
        if parent_child_dict[node] == None:
            prob_true = 0.5 #FIXME: This is a possible placeholder
            bayes_net.cpt(node).fillWith([1-prob_true, prob_true]) 
            cpt_entry["probabilities"].append({"conditions": [], "False": 1-prob_true, "True": prob_true})
        else:
            number_of_edges = len(parent_child_dict[node]) # This will get the number of edges that are going into the node
            binary_number = 0 # This will be used to keep track of the binary number that we are on
            for binary_number in range((2**number_of_edges)): # This will loop from 0 to 2^number_of_edges - 1
                binary_list = decimal_to_binary(binary_number, number_of_edges) # This will convert the decimal number to a binary number
                conditions = [f"{parent}={state}" for parent, state in zip(parent_child_dict[node], binary_list)]
                cpt_dict = dict(zip(parent_child_dict[node], binary_list)) # This will build up the dictionary that will be used to add the CPT
                bayes_true, bayes_false = bayesian_weight_calculator(cpt_dict, parent_child_weight_list, node)                 
                bayes_net.cpt(node)[cpt_dict] = [bayes_false, bayes_true] # This will add the CPT to the Bayesian network      
                cpt_entry["probabilities"].append({"conditions": conditions, "False": 1-bayes_true, "True": bayes_true})   
        cpt_data.append(cpt_entry) # This will add the CPT data to the list of CPT data
    return bayes_net, cpt_data # This will return the Bayesian network    


def get_evidence(relations_dict):
    evs = {} #This is a dictionary we can build up to store the evidence
    visibility = {} #This is a dictionary we can build up to store the visibility of the nodes
    true_visibility = [] #This is a list we can build up to store the nodes that are visible
    false_visibility = [] #This is a list we can build up to store the nodes that are not visible
    for key in relations_dict.keys():
        #There are 3 different visibility syntax's so we need to check for all of them
        if key.startswith("ref ci ca:") or key.startswith("ref ci cv:"):
            visibility[key.split()[2][3:]] = relations_dict[key].split('"')[1]
        elif key.startswith("ref ci"):
            visibility[key.split()[2]] = relations_dict[key].split('"')[1]
    
    for key in visibility.keys():
        if visibility[key] == "true":
            true_visibility.append(key)
        elif visibility[key] == "false":
            false_visibility.append(key)
    return true_visibility, false_visibility


    
def generate_pdf(bayes_net, evs):
    filename = os.path.join('static', 'bayesian_network_visualization.pdf')  # Adjust path accordingly
    img.exportInference(bayes_net, filename=filename, evs = evs, size="20")


def bayes_net_json(bayes_net, evs):
    ie = gum.LazyPropagation(bayes_net)
    ie.setEvidence(evs)
    ie.makeInference()
    
    # Prepare the nodes list
    nodes = [{'name': bayes_net.variable(node).name()} for node in bayes_net.nodes()]
    
    # Prepare the edges list
    edges = [{'from': bayes_net.variable(e[0]).name(), 'to': bayes_net.variable(e[1]).name()} for e in bayes_net.arcs()]
    
    # Compute inferences for each node
    inferences = {
        bayes_net.variable(node).name(): [round(prob*100, 2) for prob in ie.posterior(node).tolist()]
        for node in bayes_net.nodes()
    }
    
    # Append edges and inferences to each node dictionary
    for node in nodes:
        node['edges'] = [edge for edge in edges if edge['from'] == node['name']]
        node['inference'] = inferences[node['name']]
        #"inference": [
        #   false value,
        #   true value
        #]
    
    # Return the JSON representation of the nodes
    return json.dumps(nodes, indent=4)

#This acts like the main function   
def upload_and_process_file(filepath=""):
    if not filepath == "":
        bayesian_network_oml_file = open(filepath, "r")
        relationship_dict = build_relationship_dict(bayesian_network_oml_file) #This will build the relationship dictionary
        nodes, edges, parent_child_dict, parent_child_weight_list = get_nodes_and_edges(relationship_dict)
        # Nodes is a list of each node present
        # edges is a dict of all of the edges in the network where the key is the "from" node and the value is a list of "to" nodes
        # parent_child_dict is a dict of all of the edges in the network where the key is the "to" node and the value is a list of "from" nodes (this is the opposite of edges)
        # parent_child_weight_list is a list of tuples where the first element is the parent and the second element is the child and the third element is the weight of the edge
    
        #bayes_net = generate_bayes_network(relationship_dict, nodes, edges, parent_child_dict, parent_child_weight_list)  #This will generate the bayesian network
        bayes_net, cpt_data = generate_bayes_network(nodes, edges, parent_child_dict, parent_child_weight_list)  #This will generate the bayesian network
        return bayes_net, relationship_dict, cpt_data, parent_child_weight_list
    else:
        return False

