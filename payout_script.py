# %% [markdown]
# # Its On Us meal awards data analysis
# 
# data is output into the `output` folder


MAX_AMOUNT = 270

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df_awarded = pd.read_csv('input/awarded.csv', index_col=0)
df_response = pd.read_csv('input/form_responses.csv', index_col=0)

# df_response = df_response.drop_duplicates(subset='phone_number')

# %% [markdown]
# ## Two datasets, the responses and the awarded table

# %%


df_awarded.index = pd.to_datetime(df_awarded.index)



#%%

import re

df_response.index = [re.sub('2021(\S)',r'2021 \1', s) for s in df_response.index]

df_response.index = pd.to_datetime(df_response.index)
df_response
# 
# %%


t_now = df_response.index[-1]
t_last_week = t_now - np.timedelta64(1,'W')


df_r_w = df_response.loc[df_response.index > t_last_week]

df_r_w = df_r_w.drop_duplicates(subset='phone_number')

df_r_w

#%%

pn_r = df_r_w['phone_number'].value_counts().index
len(pn_r)


#%%

CDDC_phrases =[
    'cddc',
    'corvallis drop',
    'corvallis daytime'
]

dfs_out = []

for phrase in CDDC_phrases:

    df_temp = df_r_w[df_r_w['comments'].str.lower().str.contains(phrase).fillna(False)]
    dfs_out.append(df_temp)

df_payout = pd.concat(dfs_out)
df_payout

#%%

df_payout['meals'].sum()

#%%

pn_r = [pn for pn in pn_r if pn not in df_payout['phone_number'].values]

len(pn_r)

# df_r_w.drop(df_payout['phone_number'])


# %%
df_awarded.sort_index()

t_now = df_awarded.index[-1]
t_6mo = t_now - np.timedelta64(6,'M')

df_a_w = df_awarded.loc[df_awarded.index > t_6mo]
df_a_w


#%%

pn_a = df_a_w['Phone Number'].value_counts().index
pn_a



#%%

pn_0 = [pn for pn in pn_r if pn not in pn_a]



df_payout = pd.concat(
    [df_payout, df_r_w[df_r_w['phone_number'].isin(pn_0)]]
)

#%%


df_payout['meals'].sum()

#%%


counts = df_a_w['Phone Number'].value_counts().sort_values()

dfs = []

for n_awards in set(counts.values):

    pn_n = counts.where(counts==n_awards).dropna().index
    df_n = df_r_w[df_r_w['phone_number'].isin(pn_n)]
    dfs.append(df_n)

dfs

#%%


total_payout = df_payout['meals'].sum()
total_payout


df_payout_new = df_payout.copy()

for df in dfs:

    if total_payout + df['meals'].sum() > MAX_AMOUNT:
        print('hellp')
        df_last = df
        break
    else:

        df_payout_new = pd.concat(
            [df_payout_new, df]
        )

    total_payout = df_payout_new['meals'].sum()

# df_last = df_last.set_index('phone_number')
#%%

df_payout_new['meals'].sum()

#%%
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

#%%k
df_rest = df_last.loc[]
# df_rest['meals'].sum()
df_rest

#%%

df_payout['meals'].sum()
