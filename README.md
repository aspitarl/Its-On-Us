# It's On Us Corvallis 
 
It's On Us Corvallis is an organization that...

This repository contains a python script `payout_script.py` that determines the meal award distribution from the responses obtained at [the website](https://www.google.com/)

The funds are distributed to unique phone numbers and prioritized based on the number of previous awards to that phone number (zero previous awards are highest priority). Once the maximum funds are reached awards are distributed basedon a sequence of priority groups that can be found in the code. 


## Setup/Running instructions

The script needs a set of input files located in a folder `input` (that needs to be created). These files are not version controlled as they contain PII. 

`awarded.csv`: Previously awarded dataset. Has the following columns:
* Timestamp,phone_number,amount,was_gifted,,,,,,

`form_responses.csv`: The responses dataset. Has the following columns: 
* Timestamp,phone_number,meals,comments,community,statements_past_month,age_group,covid_impact,,,
