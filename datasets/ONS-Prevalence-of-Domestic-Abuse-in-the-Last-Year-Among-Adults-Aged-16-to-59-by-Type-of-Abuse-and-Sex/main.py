#!/usr/bin/env python
# coding: utf-8

# In[108]:


from gssutils import *


# In[109]:


scraper = Scraper(seed="info.json")
scraper


# In[110]:


for i in scraper.distributions:
    if '2020' in str(i.issued):
        dist = i
        print(i.title)
        print(i.issued)
#we want the 2020 dataset


# In[111]:


tabs = { tab: tab for tab in dist.as_databaker() if tab.name in ['Table 3b', 'Table 4b']}

for i in tabs:
    print(i.name)


# In[112]:


tidied_sheets = []

for tab in tabs:

    if '3b' in tab.name:
    
        pivot = tab.filter('England and Wales')

        remove = tab.filter(contains_string('Source:')).expand(RIGHT).expand(DOWN)

        sex = pivot.shift(1, 1).expand(RIGHT).is_not_blank()

        agegroup = pivot.fill(RIGHT).is_not_blank()

        period = pivot.shift(1, 3).expand(RIGHT).is_not_blank()

        assualt = pivot.shift(0, 5).expand(DOWN).is_not_blank() - remove

        disambiguation  = tab.filter(contains_string('non-sexual')) | tab.filter(contains_string('Any'))

        observations = (tab.filter(contains_string('Source:')).shift(UP).fill(RIGHT).is_not_blank().expand(UP) - period.shift(DOWN).expand(UP)).is_not_blank()

        dimensions = [
            HDim(period, 'Period', DIRECTLY, ABOVE),
            HDim(sex, 'Sex', CLOSEST, LEFT),
            HDim(assualt, 'Type of Domestic Abuse', DIRECTLY, LEFT),
            HDim(agegroup, 'Age Group', CLOSEST, ABOVE),
            HDim(disambiguation, 'Disambiguation', CLOSEST, ABOVE)
            ]
        tidy_sheet = ConversionSegment(tab, dimensions, observations)
        savepreviewhtml(tidy_sheet, fname=tab.name + " Preview.html")

        df = tidy_sheet.topandas()

        tidied_sheets.append(df)

    elif '4b' in tab.name:

        pivot = tab.filter('England and Wales')

        remove = tab.filter(contains_string('Source:')).expand(RIGHT).expand(DOWN)

        period = pivot.shift(1, 2).expand(RIGHT).is_not_blank()

        agegroup = pivot.fill(RIGHT).is_not_blank()

        assualt = pivot.shift(0, 4).expand(DOWN).is_not_blank() - remove

        disambiguation  = tab.filter(contains_string('non-sexual')) | tab.filter(contains_string('Any'))

        observations = (tab.filter(contains_string('Source:')).shift(UP).fill(RIGHT).is_not_blank().expand(UP) - period.shift(DOWN).expand(UP)).is_not_blank()

        dimensions = [
            HDim(period, 'Period', DIRECTLY, ABOVE),
            HDim(agegroup, 'Age Group', CLOSEST, ABOVE),
            HDim(assualt, 'Type of Domestic Abuse', DIRECTLY, LEFT),
            HDimConst("Sex", 'All'),
            HDim(disambiguation, 'Disambiguation', CLOSEST, ABOVE)
            ]
        tidy_sheet = ConversionSegment(tab, dimensions, observations)
        savepreviewhtml(tidy_sheet, fname=tab.name + " Preview.html")

        df = tidy_sheet.topandas()

        tidied_sheets.append(df)

df


# In[113]:


df = pd.concat(tidied_sheets)

df['Period'] = df['Period'].str.strip()

df['Period'] = df.apply(lambda x: 'government-year/20' + x['Period'][5:7] + '-20' + x['Period'][16:18] if x['Period'][16:18].isnumeric() else 'government-year/20' + x['Period'][5:7] + '-20' + x['Period'][17:19], axis = 1)

loops = 0
while loops < 3:
    df['Type of Domestic Abuse'] = df.apply(lambda x: x['Type of Domestic Abuse'][:-1] if x['Type of Domestic Abuse'][-1:].isnumeric() else x['Type of Domestic Abuse'], axis = 1)
    loops += 1

df['Age Group'] = df.apply(lambda x: ' '.join(x['Age Group'][:-1].split()[2:]) if len(x['Age Group'].split()[-1]) == 3 else ' '.join(x['Age Group'].split()[2:]), axis = 1)

df['Measure Type'] = 'percentage'
df['Unit'] = 'percent'

df['Measure Type'] = df.apply(lambda x: 'unweighted-count' if 'number of adults' in x['Type of Domestic Abuse'] else x['Measure Type'], axis = 1)
df['Unit'] = df.apply(lambda x: 'adult' if 'number of adults' in x['Type of Domestic Abuse'] else x['Unit'], axis = 1)

df = df.replace({'DATAMARKER' : {':' : 'not-applicable'},
                 'Type of Domestic Abuse' : {'Unweighted base - number of adults' : 'All',
                                             'Sexual assault by rape or penetration (including attempts)  by a partner' : 'Sexual assault by rape or penetration (including attempts) by a partner'},
                 'Sex' : {'All' : 't', 'Men' : 'm', 'Women' : 'f'},
                 'Domestic Abuse Category' : {'Unweighted base - number of adults' : 'All'}})

df['Age Group'] = df['Age Group'].apply(pathify)

df = df.rename(columns={'DATAMARKER' : 'Marker', 'OBS' : 'Value', 'Disambiguation' : 'Domestic Abuse Category'})

df['Type of Domestic Abuse'] = df.apply(lambda x: 'All' if x['Type of Domestic Abuse'] == x['Domestic Abuse Category'] else x['Type of Domestic Abuse'], axis = 1)

df['Value'] = df.apply(lambda x: 0 if x['Marker'] == 'not-applicable' else x['Value'], axis = 1)

df['Region'] = 'K04000001'

df['Domestic Abuse Category'] = df['Domestic Abuse Category'].apply(pathify)
df['Type of Domestic Abuse'] = df['Type of Domestic Abuse'].apply(pathify)

df = df[['Period', 'Region', 'Sex', 'Age Group', 'Domestic Abuse Category', 'Type of Domestic Abuse', 'Value', 'Marker', 'Measure Type', 'Unit']]

df


# In[114]:


from IPython.core.display import HTML
for col in df:
    if col not in ['Value']:
        df[col] = df[col].astype('category')
        display(HTML(f"<h2>{col}</h2>"))
        display(df[col].cat.categories)


# In[115]:


notes = """New questions were introduced into the survey from the year ending March 2013, and estimates from this year onwards are calculated using these new questions. Estimates for earlier years are calculated from the original questions with an adjustment applied to make them comparable to the new questions. From April 2017, the upper age limit for the self-completion module was increased to ask all respondents aged 16 to 74. Figures for 16 to 59 year olds only are presented in this table to allow comparisons to be made over a longer time period. A small change to the weighting procedure was made in 2019. This change is being applied going forward and was incorporated into all historic datasets. The effect of this change will only have a negligible impact on the estimates in this table and therefore historic data have not been re-calculated using the new weights, except for the year ending March 2018, where direct comparisons were previously made to the year ending March 2019. Estimates for the year ending March 2005 could not be re-calculated due to a manual adjustment which was applied to make the data comparable with the year ending 2013 onwards. More information can be found in footnote 3.	No data is available for the year ending March 2008 because comparable questions on any domestic abuse, any partner abuse and any family abuse were not included in that year. The sample size is lower for the years ending March 2011, March 2012 and March 2013 than for other years due to use of a split-sample experiment in these years. The sample size is lower for the years ending March 2018 and March 2019 due to use of a split-sample experiment. The sum of the overarching domestic abuse categories is not the sum of the sub-categories as some victims may be included in multiple categories as they can experience more than one type of abuse. The bases given are for any domestic abuse except for year ending March 2008 which is for partner abuse (non-sexual); the bases for the other measures presented will be similar."""
scraper.dataset.description = notes
scraper.dataset.title = 'Prevalence of Domestic Abuse in the Last Year Among Adults Aged 16 to 59, by Type of Abuse and Sex'

df.to_csv('observations.csv', index=False)

catalog_metadata = scraper.as_csvqb_catalog_metadata()
catalog_metadata.to_json_file('catalog-metadata.json')

