#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
import logging
import os
import phonenumbers

if not os.path.exists('output'): os.mkdir('output')

#Setup file logging that works with IPython console  https://stackoverflow.com/questions/18786912/get-output-from-the-logging-module-in-ipython-notebook
logging.basicConfig()
logger = logging.getLogger('logger')
fhandler = logging.FileHandler(filename='output/payout_script_log.log', mode='w')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fhandler.setFormatter(formatter)
logger.addHandler(fhandler)
logger.setLevel(logging.DEBUG)

logger.info('Starting Payout Script')
# %%

# Datasset of previous awards
df_prev_award = pd.read_csv('input/awarded.csv', index_col=0, encoding='utf-8')
df_prev_award.index = pd.to_datetime(df_prev_award.index)

# how far back will we include previous awards
PREV_AWARD_LOOKBACK_TIME = np.timedelta64(6,'M')
tw_awards =  df_prev_award.index[-1]- PREV_AWARD_LOOKBACK_TIME 
df_prev_award = df_prev_award.loc[df_prev_award.index > tw_awards]


#Dataset of responses
df_response = pd.read_csv('input/form_responses.csv', index_col=0, encoding='utf-8')
df_response.index = [re.sub('2021(\S)',r'2021 \1', s) for s in df_response.index]
df_response.index = pd.to_datetime(df_response.index)


# How far back will be awarding to
NEW_AWARD_LOOKBACK_TIME = np.timedelta64(28,'D')
tw_responses = df_response.index[-1] - NEW_AWARD_LOOKBACK_TIME 
df_response = df_response.loc[df_response.index > tw_responses]
df_response = df_response.drop_duplicates(subset='phone_number')

#%%

def format_PN(PN_string):
    try:
        x = phonenumbers.parse(PN_string,'US')
        formatted_str = phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.NATIONAL)

        #TODO: does phonenumbers package have the format we want to avoid this hacky mess
        formatted_str = formatted_str.replace('(','').replace(')','').replace(' ','').replace('-', '')
        return formatted_str
    except phonenumbers.NumberParseException:
        logger.info("Detected invalid phone number: {}:".format(PN_string) )

        return np.nan


df_response['phone_number'] = df_response['phone_number'].astype(str).apply(format_PN)
df_prev_award['phone_number'] = df_prev_award['phone_number'].astype(str).apply(format_PN)
#%%

# Pull out entries with these phrases in them to be paid out 
# This also forms the payout dataset (even if blank)

#These are the words we will search for in the first tier. A python list of lowercase strings
#TODO: upgrade to use regular expressions
first_tier_phrases =[
    'cddc',
    'corvallis drop',
    'corvallis daytime',
    'naacp'
    'comida'
    'alimento'
    '509j'
]

dfs_out = []

for phrase in first_tier_phrases:

    df_temp = df_response[df_response['comments'].str.lower().str.contains(phrase).fillna(False)]
    df_temp['special'] = 'first_tier'
    dfs_out.append(df_temp)

df_payout = pd.concat(dfs_out)

# df_payout.to_csv('dataset_first_tier.csv')

logger.info("{} entries found with first_tier phrases".format(len(df_payout)))

#%%

# Remove phone numbers added to payout
PN_r = df_response['phone_number'].value_counts().index
PN_r = [pn for pn in PN_r if pn not in df_payout['phone_number'].values]

logger.info("{} unique repsonse phone numbers without first_tier phrases".format(len(PN_r)))

#Immediately add phone number not in previously awarded dataset
PN_PA = df_prev_award['phone_number'].value_counts().index
PN_NA = [pn for pn in PN_r if pn not in PN_PA]

logger.info("Adding {} numbers without any awards yet".format(len(PN_NA)))

df_no_awards = df_response[df_response['phone_number'].isin(PN_NA)]
df_no_awards['num_prev_awards'] = 0

df_payout = pd.concat(
    [df_payout, df_no_awards]
)


# df_payout.info()
#%%

#Group responses by how many previous awards they had recieved
#Build payout dataset iterating through each group in order of number of awards previously received


MAX_AMOUNT = 200

logger.info("Grouping by number of previous awards until reaching {} dollars".format(MAX_AMOUNT))

total_payout = df_payout['meals'].sum()
logger.info("Total Payout so far: {}".format(total_payout))

df_payout_new = df_payout.copy()
df_last_group = None

awards_by_PN = df_prev_award['phone_number'].value_counts().sort_values()

for n_awards in set(awards_by_PN.values):

    PN_na = awards_by_PN.where(awards_by_PN==n_awards).dropna().index
    df_na = df_response[df_response['phone_number'].isin(PN_na)]
    df_na['num_prev_awards'] = n_awards
    money_na = df_na['meals'].sum()

    logger.info("{} phone numbers recieved {} Awards for a total of {} dollars".format(
        len(df_na),
        n_awards,
        money_na
        ))

    if total_payout + money_na > MAX_AMOUNT:
        logger.info('Reached maximum amount of award money')
        df_last_group = df_na#.set_index('phone_number')
        break


    df_payout_new = pd.concat(
            [df_payout_new, df_na]
        )

    total_payout = df_payout_new['meals'].sum()

df_payout = df_payout_new
#%%

#TODO: this should be a function that can be applied to each intermediate dataset

if not isinstance(df_last_group, type(None)):
    logger.info("splitting final dataset based on priority group")

    #TODO: do this earlier?
    df_last_group['age_group'] = df_last_group['age_group'].str.lower()
    df_last_group['community'] = df_last_group['community'].str.lower()

    df_last_group['special'] = 'Last Group'

    # Now for the last dataset, we group by priority group

    priority_groups = [
        ('age_group', '0 - 5'),
        ('age_group', '6-11'),
        ('age_group', '12-18'),
        ('community', 'Immigrant/Refugee'),
        ('community', 'Indigenous/Tribal'),
        ('community', 'Black, Hispanic'),
        ('community', 'Seasonal and/or'),
        ('community', 'LGBTQIA2S'),
        ('community', 'Low income adult'),
        ('community', 'Survivor')
    ]

    #TODO: sorting based on sortby key lookup instead? 

    dfs = []

    for group in priority_groups:
        group_str = group[1].lower()
        group_col = group[0]

        # If the priority group is missing, duplicate index causes issues, so just replace missing values with False to keep index the same. 
        contains_priority_str = df_last_group[group_col].str.contains(group_str)
        contains_priority_str = contains_priority_str.fillna(False)
        df_group = df_last_group[contains_priority_str]

        logger.info("Found {} entries containin {}".format(len(df_group), group_str))

        dfs.append(df_group)

    df_priority = pd.concat(dfs).drop_duplicates()

    df_payout = pd.concat(
        [df_payout, df_priority]
    )
#%%

unnamed_cols = [c for c in df_payout.columns if 'Unnamed' in c]

df_payout = df_payout.drop(['statements_past_month','covid_impact', *unnamed_cols], axis=1)

df_payout['integrated_payout'] = np.cumsum(df_payout['meals'])

df_payout.to_csv('output/payout_dataset.csv')

# %%
