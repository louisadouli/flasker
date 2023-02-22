from flask import Flask
import datetime
from flask import request as query
from flask_cors import CORS
import os
from flask import send_from_directory
from flask import url_for


x = datetime.datetime.now()
  
# Initializing flask app
app = Flask(__name__)
app = Flask(__name__, static_url_path='/static')


CORS(app)
  
# Route for seeing a data
@app.route('/')
def get_time():
  
    # Returning an api for showing in  reactjs
    return {
        'Name':"geek", 
        "Age":"22",
        "Date":x, 
        "programming":"python"
        }
  

####### Joren Van Herck, Monash University
####### Last Update: 13/04/2021

# #Imports required packages
import requests
from bs4 import BeautifulSoup
import math

@app.route('/monomers/<identifier>', methods=['GET'])
def All_Monomers(identifier) -> list:
    """Searches all monomers in database
    parameters:
    -----------
    identifier: str
        valid identifiers: name, SMILES, CAS, InChI, InChIKey, abbreviation
    
    returns:
    --------
    monomer_list: list
        list of all monomers by given identifier
    
    """
    # identifier = requests.get('id')
    iden_options = ['name', 'SMILES', 'CAS', 'InChI', 'InChIKey', 'abbreviation'] # list of valid identifiers
    if identifier not in iden_options:
        raise ValueError('Invalid Identifier ({}), use {}'.format(identifier, iden_options)) # raises ValueError if non-valid identifier is given

    monomers_request = requests.get("http://polymerdesign.de/getMonomers.php/?identifier={}".format(identifier)) # get request for getMonomers.php

    parsed_page = BeautifulSoup(monomers_request.content, 'html.parser') 
    # monomer_list=[]
    monomer_list = [i.get_text() for i in parsed_page] # creates list of all monomers
    # for i in parsed_page:
        # print(i)
        # print(i['id'])
        # monomer_list.append(i['id'])
    return monomer_list[0:len(parsed_page)-1]
@app.route('/kp/<monomer>/<identifier>')
def Monomer_kp_info(identifier: str, monomer: str) -> dict: 
    """Returns dictionary of complete monomer info
    
    Parameters:
    -----------
    
    identifier: str
        valid identifiers: name, SMILES, CAS, InChI, InChIKey, abbreviation
    monomer: str
        monomer in database (call All_Monomers function for options)
    
    returns:
    -------
        monomer_dic: dict
            dictionary of dictionaries; {coefficient: {concentration: {parameter: value}}}
        
    """
    
    iden_options = ['name', 'SMILES', 'CAS', 'InChI', 'InChIKey', 'abbreviation'] # list of valid identifiers
    if identifier not in iden_options:
        raise ValueError('Invalid Identifier ({}), use {}'.format(identifier, iden_options)) # raises ValueError if non-valid identifier is given
    
    r = requests.get("http://polymerdesign.de/getSolutionAndCoefficient.php/?id={}&monomer={}".format(identifier, monomer)) # get request for getSolution.php, variable is status code (200 if OK)

    soup = BeautifulSoup(r.content, 'html.parser') # parses content of page
    if r.content == bytes():
            raise ValueError('Monomer ({}) not in database, call All_monomer() for options'.format(monomer)) 
            
    options = soup.find_all('option')

    id_options = [i.get_text() for i in options] # creates list of all concentrations
    coefficient_dic = {}
    for coefficient in ['kp']:
        monomer_dic = {}
        for solution_ in id_options:
            sol_dic = {}
        
            data = {'identifier_':identifier  ,'monomer_select':monomer, 'coefficient_select': coefficient,'solution': solution_ }  
            r2 = requests.post('http://polymerdesign.de/index.php', data) #via mainsite, post request with identifier, monomer and loop over list of solutions

            soup_2 = BeautifulSoup(r2.content, 'html.parser') #parse content to html format

            ref = [i['href'] for i in soup_2.find_all('a') if i.text == 'Reference'][0] #text of the DOI table data is 'Reference' with embedded link to website; extract the link from the table data
            

            #extract all the data from the table
            all_td = soup_2.find_all('td') 
            all_text = [i.get_text().replace('Reference', ref).replace(' J · mol-1', '').replace('L · mol-1s-1','') for i in all_td] 

            #extract all the table headings
            all_th = soup_2.find_all('th') 
            
            ths= []
            for i in range(len(all_th)):
                try:
                    if (all_th[i]['id']) in ['main-header','temperature_th', 'kp_th']: # ignore the main table headers of the tables
                        pass
                    else:
                        ths.append(all_th[i].text)

                    
                except:
                    ths.append(all_th[i].text)


            info_dic = dict(zip(ths, all_text))
            for value in ['A', 'Ea', 'Tmin', 'Tmax']:
                try:
                    info_dic[value] = float(info_dic[value])
                except:
                    pass
            

            sol_dic = {solution_: info_dic} # combines table headers and table data (text)
            
            monomer_dic.update(sol_dic)  #get info and add to dict with solution as key and info (in form of dic (th:td)) as value (solution:{th:td})
        coefficient_dic.update({coefficient:monomer_dic}) # creates dict with the coeffiecient (here kp) as key and complete info dict of the different concentrations as value
    return coefficient_dic

@app.route('/calculate-kp')
def Calculate_kp(identifier: str, monomer: str, temperature: float) -> dict:
    """Returns calculated propagation constant(s) (kp)

    Parameters:
    -----------
    identifier: str
        valid identifiers: name, SMILES, CAS, InChI, InChIKey, abbreviation
    monomer: str
        monomer in database (call All_Monomers function for options)
    temperature: float
        temperature in degrees Celcius

    Returns
    --------
    kp_values: dict
        dict of the calculated kp values for each available concentration
    """
    kp_values = {} # creates empty dictionary
    
    monomer_info = Monomer_kp_info(identifier, monomer)['kp'] # extract kp data of the monomer

    for conc, conc_info in monomer_info.items(): # calculates the kp coeffiecent based on the extracted arrhenius parameters
        A = conc_info['A']
        ea = conc_info['Ea']
        
        x = (8.31446261815324*(273.15+temperature))
        exponent = -(ea)/x
        kp = float(A)*(math.exp(exponent))
        kp_values.update({conc:kp}) # populate the kp_values dictinary wiht the concentration as key and kp value as value
        
    return kp_values

@app.route('/data')
def data():
    # here we want to get the value of user (i.e. ?user=some-value)
    user = query.args.get('user')
    return user


@app.route('/favicon.ico')
def favicon():
    return url_for('static', filename='images/favicon.ico')
      
# Running app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')