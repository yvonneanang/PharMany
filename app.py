# app.py (Flask App)
from flask import Flask, render_template, request, jsonify
import requests
import json

app = Flask(__name__)

# Setting up api_key and api_url

existing = []
colors = []
new = []
interactions_list = []
error_msg = None
safe = False

@app.route('/')
def index():
    global safe, interactions_list, new
    return render_template('index.html', colors=colors, existing=existing, new=new, interactions_list=interactions_list, safe=safe, error_msg=error_msg)

def parse_new_drug(query):
    global error_msg
    new_drug = query
    # Parsing input string into list of search terms
    substance_name = new_drug.upper()
    
    # Parameters for the query (you can customize these based on your needs)
    query_params = {
        'api_key': api_key,
        'search': f'openfda.brand_name:"{substance_name}"',
        'limit': 1,  # Adjust the limit as needed
    }
    # Make the API request
    response = requests.get(api_url, params=query_params)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Access the JSON response
        data = response.json()

        # Process and print the data
        result = data.get('results', [])

        newdruginfo = {'Drug': substance_name, "Info": result[0]}
        error_msg=None
        return newdruginfo

    else:
        error_msg = f"Error: No data for {substance_name}. {response.status_code}, {response.text}"
        return None


def parse_existing(query):
    # Parsing input string into list of search terms
    global error_msg
    substance_names = [x.lower() for x in query]
    druglist = []

    for substance_name in substance_names:
        # Parameters for the query (you can customize these based on your needs)
        query_params = {
            'api_key': api_key,
            'search': f'openfda.brand_name:"{substance_name}"',
            'limit': 1,  # Adjust the limit as needed
        }

        # Make the API request
        response = requests.get(api_url, params=query_params)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Access the JSON response
            data = response.json()

            # Process and print the data
            result = data.get('results', [])
            druginfo = {'Drug': substance_name, "Info": result[0]}
            druglist.append(druginfo)
            error_msg = None
        else:
            error_msg = f"Error: No data for {substance_name}. {response.status_code}, {response.text}"
    return druglist

def find_active_ings(newdruginfo):
    newdrug_result = newdruginfo['Info']
    # find active ingredients of new drug
    found = False
    try:
        act_ings = newdrug_result['spl_patient_package_insert'][0].lower().split(' active ingredient:')[1].split('inactive ingredient')[0]
        found = True
    except:
        pass
    if not found:
        try:
            act_ings = newdrug_result['spl_patient_package_insert'][0].lower().split(' active ingredients:')[1].split('inactive ingredient')[0]
            found = True
        except:
            pass
    if not found:
        try:
            act_ings = newdrug_result['spl_medguide_table'][0].lower().split('>active ingredient:</content> ')[1].split('<')[0]
            found = True
        except:
            pass
    if not found:
        try:
            act_ings = newdrug_result['spl_medguide_table'][0].lower().split('>active ingredients:</content> ')[1].split('<')[0]
            found = True
        except:
            pass
    if not found:
        act_ings = newdruginfo['Drug'].lower()

    # parse active ingredients into list
    if ',' in act_ings:
        act_ings = [i.strip() for i in act_ings.split(',')]
    else:
        act_ings = [act_ings.strip()]
    return act_ings

def find_interactions(newdruginfo, druglist):
    global colors
    # find active ingredients of new drug
    interactions_list = []
    act_ings = find_active_ings(newdruginfo)

    # test active ingredients of new drug against existing drugs
    safe = True
    # search each act_ing
    for act_ing in act_ings:
    # search against each existing
        for i in range(len(druglist)):
            druginfo = druglist[i]
            try:
                interactions = druginfo['Info']['drug_interactions']
                if act_ing in interactions[0]:
                    spl_set_id = druginfo['Info']['openfda']['spl_set_id'][0]
                    interactions_list.append([i, 
                                              f"{druginfo['Drug']} interacts with the new drug because of the new drug's active ingredient {act_ing}.",
                                              f"https://nctr-crs.fda.gov/fdalabel/services/spl/set-ids/{spl_set_id}/spl-doc?hl={act_ing}#section-7.1"])
                    safe = False
                    colors[i] = "--color-dark"
            except:
                colors[i] = "--color-primary"
                pass
            if safe:
                try:
                    interactions = druginfo['Info']['drug_interactions_table']
                    if act_ing in interactions[0]:
                        spl_set_id = druginfo['Info']['openfda']['spl_set_id'][0]
                        interactions_list.append([i, 
                                              f"{druginfo['Drug']} interacts with the new drug because of the new drug's active ingredient {act_ing}.",
                                              f"https://nctr-crs.fda.gov/fdalabel/services/spl/set-ids/{spl_set_id}/spl-doc?hl={act_ing}#section-7.1"])
                        safe = False
                        colors[i] = "--color-dark"
                except:
                    pass
                    colors[i] = "--color-primary"
    print("here", interactions_list)
    return safe, interactions_list            


@app.route('/add_drug', methods=['POST'])
def add_drug():
    global safe, interactions_list, new
    drug_name = request.form.get('drug_name')
    list_type = request.form.get('list_type')

    if list_type == 'existing':
        existing.append(drug_name)
        colors.append("--color-primary")
    elif list_type == 'new':
        newdruginfo = parse_new_drug(drug_name)
        druglist = parse_existing(existing)
        safe, interactions_list = find_interactions(newdruginfo, druglist)
        new = [drug_name]

    return jsonify({'status': 'success', 'message': 'Added successfully'})

@app.route('/delete_drug', methods=['POST'])
def delete_drug():
    global safe, interactions_list, existing, new, colors
    drug_name = request.form.get('drug_name')
    list_type = request.form.get('list_type')

    if list_type == 'existing':
        existing.pop(int(drug_name))
        colors.pop(int(drug_name))
        safe=False
        interactions_list=[]
    elif list_type == 'new':
        safe = False
        interactions_list = []
        new = []
    return jsonify({'status': 'success', 'message': 'Added successfully'})

if __name__ == '__main__':
    app.run(debug=True)
