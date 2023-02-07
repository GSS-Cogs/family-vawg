#!/usr/bin/env python
# coding: utf-8

# In[63]:


from gssutils import *


# In[64]:


scraper = Scraper(seed="info.json")
scraper


# In[65]:


tabs = { tab: tab for tab in scraper.distributions[0].as_databaker() if tab.name in ['Table 3', 'Table 4']}


# In[66]:


for i in tabs:
    print(i.name)


# In[67]:


tidied_sheets = []

for tab in tabs:

    if '3' in tab.name:
    
        pivot = tab.filter('Type of abuse')

        sex = pivot.shift(RIGHT).fill(DOWN).is_not_blank()

        period = pivot.shift(2, 0).expand(RIGHT).is_not_blank()

        abuse = pivot.fill(DOWN).is_not_blank()

        abuseCat = tab.excel_ref("A8:A15") | tab.excel_ref("A24:A25") | tab.excel_ref("A34:A35") | tab.excel_ref("A44:A45") | tab.excel_ref("A58:A59")

        observations = abuse.shift(RIGHT).fill(RIGHT).is_not_blank().is_not_whitespace() - tab.filter(contains_string('Statistically significant')).expand(DOWN)

        dimensions = [
            HDim(period, 'Period', DIRECTLY, ABOVE),
            HDim(sex, 'Sex', DIRECTLY, LEFT),
            HDim(abuseCat, 'Abuse Category', CLOSEST, ABOVE),
            HDim(abuse, 'Type of Abuse', DIRECTLY, LEFT)
            ]
        tidy_sheet = ConversionSegment(tab, dimensions, observations)
        savepreviewhtml(tidy_sheet, fname=tab.name + " Preview.html")

        df = tidy_sheet.topandas()

        tidied_sheets.append(df)

    elif '4' in tab.name:

        pivot = tab.filter('Type of abuse')

        period = pivot.shift(RIGHT).expand(RIGHT).is_not_blank()

        abuse = pivot.fill(DOWN).is_not_blank()

        abuseCat = tab.excel_ref("A8:A11") | tab.excel_ref("A16") | tab.excel_ref("A21") | tab.excel_ref("A26") | tab.excel_ref("A33")

        observations = abuse.shift(RIGHT).expand(RIGHT).is_not_blank().is_not_whitespace() - tab.filter(contains_string('Statistically significant')).expand(DOWN)

        dimensions = [
            HDim(period, 'Period', DIRECTLY, ABOVE),
            HDimConst('Sex', 'all'),
            HDim(abuseCat, 'Abuse Category', CLOSEST, ABOVE),
            HDim(abuse, 'Type of Abuse', DIRECTLY, LEFT)
            ]
        tidy_sheet = ConversionSegment(tab, dimensions, observations)
        savepreviewhtml(tidy_sheet, fname=tab.name + " Preview.html")

        df = tidy_sheet.topandas()

        tidied_sheets.append(df)

df


# In[83]:


import re

df = pd.concat(tidied_sheets)

df['Period'] = df['Period'].str.strip()

#df['Period'] = df.apply(lambda x: 'government-year/20' + x['Period'][5:7] + '-20' + x['Period'][16:18] if x['Period'][16:18].isnumeric() else 'government-year/20' + x['Period'][5:7] + '-20' + x['Period'][17:19], axis = 1)

df['Period'] = df.apply(lambda x: re.sub(r'[\(\[].*?[\)\]]', '', x['Period']), axis =1)
df['Abuse Category'] = df.apply(lambda x: re.sub(r'[\(\[].*?[\)\]]', '', x['Abuse Category']), axis =1)
df['Type of Abuse'] = df.apply(lambda x: re.sub(r'[\(\[].*?[\)\]]', '', x['Type of Abuse']), axis =1)

df['Period'] = df.apply(lambda x: x['Period'].replace('\n', '').replace('toMar', 'to Mar'), axis = 1)

df['Period'] = df.apply(lambda x: 'government-year/' + str(x['Period'])[4:8] + '-' + str(x['Period'])[16:20], axis = 1)

df['Measure Type'] = 'percentage'
df['Unit'] = 'percent'

df['Abuse Category'] = df['Abuse Category'].str.strip().str.replace('  ' , ' ')

df['Type of Abuse'] = df['Type of Abuse'].str.strip().str.replace('  ' , ' ')

df = df.replace({'Sex' : {'All' : 't', 'Men' : 'm', 'Women' : 'f'},
                'Type of Abuse' : {'Unweighted base - number of adults' : 'All',
                                   'Sexual assault by rape or penetration  by a partner' : 'Sexual assault by rape or penetration by a partner'},
                'DATAMARKER' : {'[x]' : 'not-available',
                                '[c]' : 'suppressed',
                                '[z]' : 'not-applicable'}})

df = df.rename(columns={'DATAMARKER' : 'Marker', 'OBS' : 'Value'})

df['Type of Abuse'] = df.apply(lambda x: 'all' if x['Type of Abuse'] == x['Abuse Category'] else x['Type of Abuse'], axis = 1)

df['Age Group'] = '16 to 59'

df['Region'] = 'K04000001'

df = df[['Period', 'Region', 'Sex', 'Age Group', 'Abuse Category', 'Type of Abuse', 'Value', 'Marker', 'Measure Type', 'Unit']]

df['Value'] = df.apply(lambda x: x['Value'] if pd.isnull(x['Marker']) else 0.0, axis = 1)

df['Value'] = df['Value'].round(1)

df


# In[84]:


from IPython.core.display import HTML
for col in df:
    if col not in ['Value']:
        df[col] = df[col].astype('category')
        display(HTML(f"<h2>{col}</h2>"))
        display(df[col].cat.categories)


# In[70]:


notes = """New questions were introduced into the survey from the year ending March 2013, and estimates from this year onwards are calculated using these new questions. Estimates for earlier years are calculated from the original questions with an adjustment applied to make them comparable to the new questions. From April 2017, the upper age limit for the self-completion module was increased to ask all respondents aged 16 to 74. Figures for 16 to 59 year olds only are presented in this table to allow comparisons to be made over a longer time period. A small change to the weighting procedure was made in 2019. This change is being applied going forward and was incorporated into all historic datasets. The effect of this change will only have a negligible impact on the estimates in this table and therefore historic data have not been re-calculated using the new weights, except for the year ending March 2018, where direct comparisons were previously made to the year ending March 2019. Estimates for the year ending March 2005 could not be re-calculated due to a manual adjustment which was applied to make the data comparable with the year ending 2013 onwards. More information can be found in footnote 3.	No data is available for the year ending March 2008 because comparable questions on any domestic abuse, any partner abuse and any family abuse were not included in that year. The sample size is lower for the years ending March 2011, March 2012 and March 2013 than for other years due to use of a split-sample experiment in these years. The sample size is lower for the years ending March 2018 and March 2019 due to use of a split-sample experiment. The sum of the overarching domestic abuse categories is not the sum of the sub-categories as some victims may be included in multiple categories as they can experience more than one type of abuse. The bases given are for any domestic abuse except for year ending March 2008 which is for partner abuse (non-sexual); the bases for the other measures presented will be similar."""
scraper.dataset.description = notes
scraper.dataset.title = 'Prevalence of Domestic Abuse in the Last Year Among Adults Aged 16 to 59, by Type of Abuse and Sex'

df.to_csv('observations.csv', index=False)

catalog_metadata = scraper.as_csvqb_catalog_metadata()
catalog_metadata.to_json_file('catalog-metadata.json')

