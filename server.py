from flask import Flask, request, redirect, url_for, render_template, jsonify
import os
import atexit
import UABayesViewEngine as bnViz

app = Flask(__name__)

# Ensure the upload directory exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def cleanup_uploads_folder(): #Cleanup the uploads folder when the server is shut down
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

# Register the cleanup function with atexit
atexit.register(cleanup_uploads_folder)

#This is a helper function that will load the bayesian network data and the relationship dictionary
def load_bayes_net(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    return bnViz.upload_and_process_file(filepath)


def prepare_weight_data(parent_child_weight_list):
    weight_data = {}
    for parent, child, weight in parent_child_weight_list:
        if child not in weight_data:
            weight_data[child] = {'parents': [], 'weights': [], 'total_weight': 0}
        weight_data[child]['parents'].append(parent)
        weight_data[child]['weights'].append(weight)
        weight_data[child]['total_weight'] += weight
    return weight_data


#Display the index page
@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

#This will make it so the SIE image will return home when clicked
@app.route('/')
def home():
    return render_template("index.html")


#This is the route for the upload page that will take in a user's OML file
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        file = request.files.get('file')
        if file and file.filename.endswith('.oml'):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            
            # Redirect to the selection page, passing the filename as a query parameter
            return redirect(url_for('display_weights', filename=file.filename))
    
    # For GET or failed POST requests
    return render_template('upload.html')


@app.route('/weight', methods=['GET'])
def display_weights():
    filename = request.args.get('filename', '') if request.method == 'GET' else request.form.get('filename', '')
    _, _, _, parent_child_weight_list = load_bayes_net(filename)
    weight_data = prepare_weight_data(parent_child_weight_list)
    return render_template('weights.html', weight_data=weight_data, filename=filename)


@app.route('/select', methods=['GET', 'POST'])
def select_options():
    filename = request.args.get('filename', '') if request.method == 'GET' else request.form.get('filename', '')
    _, relationship_dict, _, _ = load_bayes_net(filename) #call the helper function but we only need the relationship dictionary
    
    if request.method == 'POST':
        selections = {}
        for key, value in request.form.items():
            if value == "0":
                selections[key] = 0
            elif value == "1":
                selections[key] = 1
    #This section of logic is building up the evidance dictionary that takes user input from the radio buttons
        
    radio_button_nodes, invisible_nodes = bnViz.get_evidence(relationship_dict)
    sets_of_options = [{'name': node, 'options': ['False', 'True', 'N/A']} for node in radio_button_nodes]
    
    return render_template('select.html', sets_of_options=sets_of_options, filename=filename, invisible_nodes=invisible_nodes)


@app.route('/get_bayes_JSON', methods=['POST'])
def get_bayes_json():
    raw_selections = request.get_json()
    filename = raw_selections.pop('filename', '')

    if not filename:
        return jsonify({'error': 'Filename is required'}), 400

    selections = {key: int(value) for key, value in raw_selections.items() if value != "2"} # 2 is N/A value
    bayes_net, _, _ , _ = load_bayes_net(filename)  # Assuming this function can handle selections
    bayes_net_data = bnViz.bayes_net_json(bayes_net, selections)
    return jsonify(bayes_net_data)


#This is a route to display the conditional probability table
@app.route('/show_CPTs', methods=['GET'])
def show_CPTs():
    filename = request.args.get('filename', '')
    # Assuming load_bayes_net function correctly handles the file and returns the desired data
    _, _, cpt_data, _ = load_bayes_net(filename)
    return render_template('cpt.html', cpts=cpt_data, filename=filename)



if __name__ == '__main__':
    #FIXME: this will probably need to be changed. This is just for development purposes
    app.run(host="0.0.0.0", port=8000)