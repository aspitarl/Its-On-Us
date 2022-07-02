#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
import logging

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
df_prev_award = pd.read_csv('input/awarded.csv', index_col=0)
df_prev_award.index = pd.to_datetime(df_prev_award.index)

# how far back will we include previous awards
PREV_AWARD_LOOKBACK_TIME = np.timedelta64(6,'M')
tw_awards =  df_prev_award.index[-1]- PREV_AWARD_LOOKBACK_TIME 
df_prev_award = df_prev_award.loc[df_prev_award.index > tw_awards]


#Dataset of responses
df_response = pd.read_csv('input/form_responses.csv', index_col=0)
df_response.index = [re.sub('2021(\S)',r'2021 \1', s) for s in df_response.index]
df_response.index = pd.to_datetime(df_response.index)
df_response = df_response.drop_duplicates(subset='phone_number')

# How far back will be awarding to
NEW_AWARD_LOOKBACK_TIME = np.timedelta64(10,'W')
tw_responses = df_response.index[-1] - NEW_AWARD_LOOKBACK_TIME 
df_response = df_response.loc[df_response.index > tw_responses]


#%%

# Pull out entries with these phrases in them to be paid out 
# This also forms the payout dataset (even if blank)

CDDC_phrases =[
    'cddc',
    'corvallis drop',
    'corvallis daytime'
]

dfs_out = []

for phrase in CDDC_phrases:

    df_temp = df_response[df_response['comments'].str.lower().str.contains(phrase).fillna(False)]
    dfs_out.append(df_temp)

df_payout = pd.concat(dfs_out)

logger.info("{} entries found with CDDC phrases".format(len(df_payout)))

#%%

# Remove phone numbers added to payout
PN_r = df_response['phone_number'].value_counts().index
PN_r = [pn for pn in PN_r if pn not in df_payout['phone_number'].values]

logger.info("{} unique repsonse phone numbers without CDDC phrases".format(len(PN_r)))

#Immediately add phone number not in previously awarded dataset
PN_PA = df_prev_award['phone_number'].value_counts().index
PN_NA = [pn for pn in PN_r if pn not in PN_PA]

logger.info("Adding {} numbers without any awards yet".format(len(PN_NA)))


df_payout = pd.concat(
    [df_payout, df_response[df_response['phone_number'].isin(PN_NA)]]
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
    money_na = df_na['meals'].sum()

    logger.info("{} phone numbers recieved {} Awards for a total of {} dollars".format(
        len(df_na),
        n_awards,
        money_na
        ))

    if total_payout + money_na > MAX_AMOUNT:
        logger.info('Reached maximum amount of award money')
        df_last = df_na.set_index('phone_number')
        break


    df_payout_new = pd.concat(
            [df_payout_new, df_na]
        )

    total_payout = df_payout_new['meals'].sum()

#%%

if not isinstance(df_last, type(None)):
    logger.info("splitting final dataset based on priority group")

    #TODO: do this earlier?
    df_last['age_group'] = df_last['age_group'].str.lower()
    df_last['community'] = df_last['community'].str.lower()

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

    dfs = []

    for group in priority_groups:
        group_str = group[1].lower()
        group_col = group[0]

        df_group = df_last[df_last[group_col].str.contains(group_str)]
        dfs.append(df_group)

    df_priority = pd.concat(dfs).drop_duplicates()


    df_priority['meals'].sum()


    df_priority

#%%

df_priority