#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re


# %%

# Datasset of previous awards
df_prev_award = pd.read_csv('input/awarded.csv', index_col=0)
df_prev_award.index = pd.to_datetime(df_prev_award.index)

# how far back will we include previous awards
#TODO: do we also need to exclude the response dataset from this reference?
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
df_payout
#%%

# Remove phone numbers added to payout
PN_r = df_response['phone_number'].value_counts().index
PN_r = [pn for pn in PN_r if pn not in df_payout['phone_number'].values]

#remove phone numbers in awarded dataset (see TODO above)
PN_a = df_prev_award['Phone Number'].value_counts().index
PN_0 = [pn for pn in PN_r if pn not in PN_a]

df_payout = pd.concat(
    [df_payout, df_response[df_response['phone_number'].isin(PN_0)]]
)

df_payout.info()
#%%

#Group responses by how many previous awards they had recieved
#Build payout dataset iterating through each group in order of number of awards previously received

MAX_AMOUNT = 50 #270


total_payout = df_payout['meals'].sum()
df_payout_new = df_payout.copy()

awards_by_PN = df_prev_award['Phone Number'].value_counts().sort_values()

for n_awards in set(awards_by_PN.values):

    PN_n = awards_by_PN.where(awards_by_PN==n_awards).dropna().index
    df_n = df_response[df_response['phone_number'].isin(PN_n)]

    if total_payout + df_n['meals'].sum() > MAX_AMOUNT:
        print('Reached maximum amount of award money')
        df_last = df_n
        break

    df_payout_new = pd.concat(
            [df_payout_new, df_n]
        )

    total_payout = df_payout_new['meals'].sum()

df_last = df_last.set_index('phone_number')
#%%

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

    df_group = df_last[df_last[group[0]].str.lower().str.contains(group[1].lower())]
    dfs.append(df_group)

df_priority = pd.concat(dfs).drop_duplicates()


df_priority['meals'].sum()

#%%
[pn for pn in df_last.index.values if pn not in df_priority.index.values]

#%%

df_payout['meals'].sum()

# %%
