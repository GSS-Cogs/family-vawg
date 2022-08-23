#!/usr/bin/env python
# coding: utf-8

# In[1]:


from gssutils import *
from datetime import date


# In[2]:


def cell_to_string(cell):
    s = str(cell)
    start = s.find("'") + len("'")
    end = s.find(">")
    substring = s[start:end].strip("'")
    return substring

months = {'January' : '01', 
          'February' : '02', 
          'March'    : '03',
          'April'    : '04',
          'May'      : '05',
          'June'     : '06',
          'July'     : '07',
          'August'   : '08',
          'September': '09',
          'October'  : '10',
          'November' : '11',
          'December' : '12'}


# In[3]:


scraper = Scraper(seed="info.json")
scraper


# In[4]:


for i in scraper.distributions:
    print(i.title)
    print(i.issued)


# In[5]:


tabs = { tab: tab for tab in scraper.distributions[0].as_databaker() if '3a' in tab.name}
for i in tabs:
    print(i.name)


# In[6]:


tidied_sheets = []

for tab in tabs:
    
    pivot = tab.filter('Personal characteristic row')

    period = cell_to_string(tab.excel_ref("A2"))
    
    for word, number in months.items():
        period = period.replace(word, number)

    periodRange = period.split()

    periodRange = [int(i) for i in periodRange if i.isnumeric() == True]

    a = date(periodRange[4],periodRange[1],periodRange[0])
    b = date(periodRange[4],periodRange[3],periodRange[2])

    periodRange = -(a-b).days

    harassment = pivot.fill(RIGHT).is_not_blank()

    characteristic = pivot.fill(DOWN).is_not_blank()

    observations = harassment.fill(DOWN).is_not_blank() - tab.filter(contains_string('significance of change')).fill(DOWN)

    char = characteristic - observations.expand(LEFT) | pivot.shift(DOWN)

    change = tab.filter('Personal characteristic row').expand(RIGHT).is_not_blank().shift(RIGHT).fill(DOWN) -             (tab.filter(contains_string('%')).fill(DOWN) |             tab.filter(contains_string('number of adults')).fill(DOWN) |             tab.filter('None of the above significance of change compared to June 2021').fill(DOWN))

    dimensions = [
        HDimConst('Period', period),
        HDimConst('Period Range', periodRange),
        HDim(harassment, 'Harassment', DIRECTLY, ABOVE),
        HDim(characteristic, 'Characteristic', DIRECTLY, LEFT),
        HDim(char, 'Char', CLOSEST, ABOVE),
        HDim(change, 'Change', DIRECTLY, RIGHT)
        ]
    tidy_sheet = ConversionSegment(tab, dimensions, observations)
    savepreviewhtml(tidy_sheet, fname=tab.name + " Preview.html")

    tidied_sheets.append(tidy_sheet.topandas())


# In[7]:


df = pd.concat(tidied_sheets)

dataframes = []
all         = df[ df['Char'] == 'ALL ADULTS' ]
all = all.rename(columns={'Characteristic' : all['Char'].unique()[0]})
all = all.drop(  columns=['Char'])
dataframes.append(all)
ageandsex   = df[ df['Char'] == 'Age and sex' ]
ageandsex = ageandsex.rename(columns={'Characteristic' : ageandsex['Char'].unique()[0]})
ageandsex = ageandsex.drop(  columns=['Char'])
dataframes.append(ageandsex)
Age         = df[ df['Char'] == 'Age group' ]
Age = Age.rename(columns={'Characteristic' : Age['Char'].unique()[0]})
Age = Age.drop(  columns=['Char'])
dataframes.append(Age)
deprivation = df[ df['Char'] == 'Deprivation [note 6]' ]
deprivation = deprivation.rename(columns={'Characteristic' : deprivation['Char'].unique()[0]})
deprivation = deprivation.drop(  columns=['Char'])
dataframes.append(deprivation)
disability  = df[ df['Char'] == 'Disability' ]
disability = disability.rename(columns={'Characteristic' : disability['Char'].unique()[0]})
disability = disability.drop(  columns=['Char'])
dataframes.append(disability)
ethnic      = df[ df['Char'] == 'Ethnic group' ]
ethnic = ethnic.rename(columns={'Characteristic' : ethnic['Char'].unique()[0]})
ethnic = ethnic.drop(  columns=['Char'])
dataframes.append(ethnic)
region      = df[ df['Char'] == 'Region' ]
region = region.rename(columns={'Characteristic' : region['Char'].unique()[0]})
region = region.drop(  columns=['Char'])
dataframes.append(region)

df = pd.concat(dataframes).fillna('')

# I had a better way to do the above but my brain is melting and I cant remember how to pivot the thing without it being a nightmare

df['Region'] = df.apply(lambda x: x['Period'].split(',')[0] if x['Region'] == '' else x['Region'], axis = 1)

df['Period'] = df['Period'].str.split(',', expand=True)[1].str.strip()

df['Period'] = df.apply(lambda x: 'gregorian-interval/' + x['Period'].split()[5] + '-' + x['Period'].split()[1] + '-' + x['Period'].split()[0] + 'T00:00:00/P' + str(x['Period Range']) + 'D', axis = 1)

df = df.rename(columns={'OBS' : 'Value', 'DATAMARKER' : 'Marker', 'ALL ADULTS' : 'Sex', 'Deprivation [note 6]' : 'Deprivation', 'Age group' : 'Age Group', 'Ethnic group' : 'Ethnic Group'})

df['Sex'] = df.apply(lambda x: 'Male' if 'Male' in x['Age and sex'] else ('Female' if 'Female' in x['Age and sex'] else x['Sex']), axis = 1)

df['Age and sex'] = df['Age and sex'].str.split('aged', expand=True)[1]

df['Age Group'] = df.apply(lambda x: x['Age and sex'] if x['Age Group'] == '' else x['Age Group'], axis = 1).fillna('')
df['Age Group'] = df['Age Group'].str.strip()

df['Measure Type'] = df.apply(lambda x: 'percentage' if '%' in x['Harassment'] else ('unweighted-count' if 'number' in x['Harassment'] else ''), axis = 1)
df['Unit'] = df.apply(lambda x: 'percent' if '%' in x['Harassment'] else ('adult' if 'number' in x['Harassment'] else ''), axis = 1)

df['Harassment'] = df['Harassment'].str.replace(r'\(.*\).*', '')
df['Harassment'] = df['Harassment'].str.replace('\n', '')
df['Harassment'] = df['Harassment'].str.replace(r'\[.*\].*', '')
df['Harassment'] = df['Harassment'].str.strip()

df = df.replace({'Region' : {'Great Britain' : 'K03000001',
                             'East of England' : 'E12000006',
                             'East Midlands' : 'E12000004',
                             'London' : 'E12000007',
                             'North East' : 'E12000001',
                             'North West' : 'E12000002',
                             'South East' : 'E12000008',
                             'South West' : 'E12000009',
                             'West Midlands' : 'E12000005',
                             'Yorkshire and The Humber' : 'E12000003',
                             'Scotland' : 'S92000003',
                             'Wales' : 'W92000004'},
                 'Harassment' : {'Unweighted base - number of adults' : 'All'},
                 'Marker' : {'' : 'N/A'},
                 'Change' : {'' : 'N/A'},
                 'Sex' : {'ALL ADULTS' : 't', 'All' : 't', 'Men' : 'm', 'Women' : 'f'}})})

df = df.drop(['Period Range', 'Age and sex'], axis = 1)

df['Value'] = df.apply(lambda x: 0 if '[c]' in x['Marker'] else x['Value'], axis = 1)
df['Marker'] = df.apply(lambda x: '[s]' if '[' in x['Change'] else x['Marker'], axis = 1)

df = df.rename(columns={'Change' : 'Change Marker'})

df = df.replace('', 'All')
df = df.replace('N/A' , '')

df['Age Group'] = df['Age Group'].apply(pathify)

df = df[['Period', 'Region', 'Harassment', 'Sex', 'Age Group', 'Disability', 'Deprivation', 'Ethnic Group', 'Value', 'Marker', 'Change Marker', 'Measure Type', 'Unit']]

df = df[df['Measure Type'].str.contains("All")==False]

df


# In[8]:


from IPython.core.display import HTML
for col in df:
    if col not in ['Value']:
        df[col] = df[col].astype('category')
        display(HTML(f"<h2>{col}</h2>"))
        display(df[col].cat.categories)


# In[9]:


notes = """Please note percentages may not sum to 100% due to rounding. There are cases in which respondents do not answer a specific question. Where this happens, they have been excluded from the analysis. As a result, the unweighted bases for some categories may not sum to the total. Percentages may not sum to 100% as respondents could select multiple response options. [c] indicates where individual estimates have been suppressed on quality grounds and to avoid disclosure issues. Figures are based on a small number of respondents (< 3). [s] indicates there is a statistically significant change at the 5% level, [d]  a statistical decrease and [i] a statistical increase. [z] indicates not applicable as significant testing not possible. """
scraper.dataset.title = "Prevalence of Harassment in the last year among all adults"
scraper.dataset.description = notes

df.to_csv('observations.csv', index=False)

catalog_metadata = scraper.as_csvqb_catalog_metadata()
catalog_metadata.to_json_file('catalog-metadata.json')

