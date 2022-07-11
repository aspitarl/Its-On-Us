# It's On Us Corvallis 
 
It's On Us Corvallis is food aid for the 21st century.

Anyone in Benton County, Oregon, can enter a weekly drawing to win a gift card for food. Gift cards are distrbuted using payment app [Kuto](https://kuto.app/) and can be used at select locally owned food businesses in Benton County. People can use these gift cards to purchase the food they want, where they want, when they want.

This repository contains a python script `payout_script.py` that determines the gift card award distribution from the responses obtained at [the website](https://itsonuscorvallis.org/eat)

Funds distributed are raised by volunteers from community donations, [Benton Community Foundation](https://www.bcfgives.org/), and funding from the American Rescue Plan Act (ARPA) distributed by Benton County. 

The funds are distributed to unique phone numbers and prioritized based on the number of previous awards to that phone number (zero previous awards are highest priority). Once the maximum funds are reached awards are distributed basedon a sequence of priority groups that can be found in the code. 

IOU Corvallis is volunteer-run project of the Food Action Team, one of 12 action teams of the [Corvallis Sustainability Coalition](https://sustainablecorvallis.org/). 

## Setup/Running instructions

The script needs a set of input files located in a folder `input` (that needs to be created). These files are not version controlled as they contain PII. 

This means all identifying information such as phone number, comments, and demographics are never shared online and are secure.

`awarded.csv`: Previously awarded dataset. Has the following columns:
* Timestamp,phone_number,amount,was_gifted,,,,,,

`form_responses.csv`: The responses dataset. Has the following columns: 
* Timestamp,phone_number,meals,comments,community,statements_past_month,age_group,covid_impact,,,
