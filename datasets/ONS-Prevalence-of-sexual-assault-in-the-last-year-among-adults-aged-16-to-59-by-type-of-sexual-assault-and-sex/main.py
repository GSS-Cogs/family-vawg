#!/usr/bin/env python
# coding: utf-8

# In[135]:


from gssutils import *


# In[136]:


scraper = Scraper(seed="info.json")
scraper


# In[137]:


for i in scraper.distributions:
    print(i.title)
    print(i.issued)


# In[138]:


tabs = { tab: tab for tab in scraper.distributions[0].as_databaker() if tab.name in ['Table 3b', 'Table 4b']}
for i in tabs:
    print(i.name)


# In[139]:


tidied_sheets = []

for tab in tabs:

    if '3b' in tab.name:
    
        pivot = tab.filter('England and Wales')

        remove = tab.filter(contains_string('Source:')).expand(RIGHT).expand(DOWN)

        sex = tab.filter('Men') | tab.filter('Women').shift(LEFT).expand(RIGHT)

        sex_override = {'': 'Women'}

        agegroup = pivot.fill(RIGHT).is_not_blank()

        period = pivot.shift(1, 3).expand(RIGHT).is_not_blank()

        assualt = pivot.shift(0, 6).expand(DOWN).is_not_blank() - remove

        observations = (tab.filter(contains_string('Source:')).shift(UP).fill(RIGHT).is_not_blank().expand(UP) - period.shift(DOWN).expand(UP)).is_not_blank()

        dimensions = [
            HDim(period, 'Period', DIRECTLY, ABOVE),
            HDim(sex, 'Sex', CLOSEST, LEFT, cellvalueoverride=sex_override),
            HDim(assualt, 'Type of Sexual Assualt', DIRECTLY, LEFT),
            HDim(agegroup, 'Age Group', CLOSEST, ABOVE),
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

        assualt = pivot.shift(0, 5).expand(DOWN).is_not_blank() - remove

        observations = (tab.filter(contains_string('Source:')).shift(UP).fill(RIGHT).is_not_blank().expand(UP) - period.shift(DOWN).expand(UP)).is_not_blank()

        dimensions = [
            HDim(period, 'Period', DIRECTLY, ABOVE),
            HDim(agegroup, 'Age Group', CLOSEST, ABOVE),
            HDim(assualt, 'Type of Sexual Assualt', DIRECTLY, LEFT),
            HDimConst("Sex", 'All')
            ]
        tidy_sheet = ConversionSegment(tab, dimensions, observations)
        savepreviewhtml(tidy_sheet, fname=tab.name + " Preview.html")

        df = tidy_sheet.topandas()

        tidied_sheets.append(df)

df


# In[140]:


df = pd.concat(tidied_sheets)

df['Period'] = df['Period'].str.strip()

df['Period'] = df.apply(lambda x: 'government-year/20' + x['Period'][5:7] + '-20' + x['Period'][16:18] if x['Period'][16:18].isnumeric() else 'government-year/20' + x['Period'][5:7] + '-20' + x['Period'][17:19], axis = 1)

df['Type of Sexual Assualt'] = df['Type of Sexual Assualt'].str.replace('-', '')
df['Type of Sexual Assualt'] = df['Type of Sexual Assualt'].str.replace('  ', ' ')
df['Type of Sexual Assualt'] = df['Type of Sexual Assualt'].str.strip()

loops = 0
while loops < 3:
    df['Type of Sexual Assualt'] = df.apply(lambda x: x['Type of Sexual Assualt'][:-1] if x['Type of Sexual Assualt'][-1:].isnumeric() else x['Type of Sexual Assualt'], axis = 1)
    loops += 1

df['Age Group'] = df.apply(lambda x: ' '.join(x['Age Group'][:-1].split()[2:]) if len(x['Age Group'].split()[-1]) == 3 else ' '.join(x['Age Group'].split()[2:]), axis = 1)

df['Measure Type'] = 'percentage'
df['Unit'] = 'percent'

df['Measure Type'] = df.apply(lambda x: 'unweighted count' if 'number of adults' in x['Type of Sexual Assualt'] else x['Measure Type'], axis = 1)
df['Unit'] = df.apply(lambda x: 'adult' if 'number of adults' in x['Type of Sexual Assualt'] else x['Unit'], axis = 1)

df = df.replace({'DATAMARKER' : {':' : 'not-applicable'},
                 'Type of Sexual Assualt' : {'Unweighted base number of adults' : 'All'}})

df = df.rename(columns={'DATAMARKER' : 'Marker', 'OBS' : 'Value'})

df['Value'] = df.apply(lambda x: 0 if x['Marker'] == 'not-applicable' else x['Value'], axis = 1)

df['Region'] = 'K04000001'

df = df[['Period', 'Region', 'Sex', 'Age Group', 'Type of Sexual Assualt', 'Value', 'Marker', 'Measure Type', 'Unit']]

df


# In[141]:


from IPython.core.display import HTML
for col in df:
    if col not in ['Value']:
        df[col] = df[col].astype('category')
        display(HTML(f"<h2>{col}</h2>"))
        display(df[col].cat.categories)


# In[144]:


notes = """From April 2017, the upper age limit for the self-completion module has been increased to ask all respondents aged 16 to 74. Figures for 16 to 59 year olds only are presented in this table to allow comparisons to be made over a longer time period. The sample size is lower from year ending March 2011 to year ending March 2013 due to use of a split-sample experiment. The accompanying methodological note provides further information. The sample size is lower for year ending March 2018 and March 2019 due to use of a split-sample experiment. From the year ending March 2013, estimates of indecent exposure and unwanted touching are split out into separate categories. Previous combined estimates are still provided to make them comparable to earlier years. Estimates are calculated from the new questions from year ending March 2013 onwards. Previous estimates are calculated from the original questions and an adjustment applied to make them comparable to the new questions. As such, figures prior to year ending March 2013 may differ to those previously published."""
scraper.dataset.description = notes
scraper.dataset.title = 'Prevalence of sexual assault in the last year among adults aged 16 to 59, by type of sexual assault and sex'

df.to_csv('observations.csv', index=False)

catalog_metadata = scraper.as_csvqb_catalog_metadata()
catalog_metadata.to_json_file('catalog-metadata.json')


# In[143]:


###
# Theres a conversation to be had about whether or not to try and include the 'compared to previous years markers'																
###

