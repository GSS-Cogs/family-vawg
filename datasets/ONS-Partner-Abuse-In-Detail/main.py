#!/usr/bin/env python
# coding: utf-8

# In[17]:


from gssutils import *


# In[18]:


scraper = Scraper(seed="info.json")
scraper


# In[19]:


for i in scraper.distributions:
    print(i.title)
    print(i.issued)


# In[20]:


tabs = { tab: tab for tab in scraper.distributions[0].as_databaker() if tab.name in ['Table 12']}

for i in tabs:
    print(i.name)


# In[21]:


tidied_sheets = []

for tab in tabs:
    
    pivot = tab.filter('England and Wales')

    remove = tab.filter(contains_string('Source:')).expand(RIGHT).expand(DOWN)

    sex = pivot.shift(1, 1).expand(RIGHT).is_not_blank()

    agegroup = pivot.fill(RIGHT).is_not_blank()

    partner_abuse = pivot.shift(0, 3).expand(DOWN).is_not_blank() - remove

    period = 'government-year/2017-2018'

    observations = sex.waffle(partner_abuse)

    dimensions = [
        HDim(sex, 'Sex', CLOSEST, LEFT),
        HDim(partner_abuse, 'Partner Abuse', DIRECTLY, LEFT),
        HDim(agegroup, 'Age Group', CLOSEST, ABOVE),
        HDimConst("Period", period)
        ]

    tidy_sheet = ConversionSegment(tab, dimensions, observations)
    savepreviewhtml(tidy_sheet, fname=tab.name + " Preview.html")

    df = tidy_sheet.topandas()

    tidied_sheets.append(df)

df


# In[22]:


df = pd.concat(tidied_sheets)

df = df.rename(columns={'OBS' : 'Value'})

loops = 0
while loops < 3:
    df['Partner Abuse'] = df.apply(lambda x: x['Partner Abuse'][:-1] if x['Partner Abuse'][-1:].isnumeric() else x['Partner Abuse'], axis = 1)
    loops += 1

df['Age Group'] = df.apply(lambda x: ' '.join(x['Age Group'][:-1].split()[2:]) if len(x['Age Group'].split()[-1]) == 3 else ' '.join(x['Age Group'].split()[2:]), axis = 1)

df['Measure Type'] = 'percentage'
df['Unit'] = 'percent'

df['Measure Type'] = df.apply(lambda x: 'unweighted count' if 'number of adults' in x['Partner Abuse'] else x['Measure Type'], axis = 1)
df['Unit'] = df.apply(lambda x: 'adult' if 'number of adults' in x['Partner Abuse'] else x['Unit'], axis = 1)

df = df.replace({'Partner Abuse' : {'Unweighted base - number of adults' : 'All'},
                 'Sex' : {'All' : 't', 'Men' : 'm', 'Women' : 'f'}})

df['Region'] = 'K04000001'

df = df[['Period', 'Region', 'Sex', 'Age Group', 'Partner Abuse', 'Value', 'Measure Type', 'Unit']]

df


# In[23]:


from IPython.core.display import HTML
for col in df:
    if col not in ['Value']:
        df[col] = df[col].astype('category')
        display(HTML(f"<h2>{col}</h2>"))
        display(df[col].cat.categories)


# In[24]:


notes = """This question was asked of abuse experienced in the last 12 months. Due to changes in questionnaire structure, estimates on these questions are not comparable with data prior to year ending March 2011. Unweighted base refers to question on whether victim told someone known personally. Other bases are similar."""
scraper.dataset.description = notes
scraper.dataset.title = 'Partner Abuse In Detail'

df.to_csv('observations.csv', index=False)

catalog_metadata = scraper.as_csvqb_catalog_metadata()
catalog_metadata.to_json_file('catalog-metadata.json')

