
# %%
import pandas as pd
import numpy as np
from collections import defaultdict
from slugify import slugify
from html2text import unescape
import re

# Shopify CSV Format https://help.shopify.com/en/manual/products/import-export/using-csv#import-csv-files-into-google-sheets
# %%
WC_EXPORT_CSV = 'wc-export/wc-export-product-aw.csv'
SHOPIFY_IMPORT_CSV = 'shopify-import/shopify-import-aw.csv'
SHOPIFY_EXAMPLE_CSV = 'shopify-example.csv'
shopify_example_data = pd.read_csv(SHOPIFY_EXAMPLE_CSV)
wc_full_data = pd.read_csv(WC_EXPORT_CSV)
shopify_data = pd.DataFrame()
# print(wc_full_data['Visibility in catalog'].dtypes)

# %%
# wc_data Clean UP
wc_full_data = wc_full_data.sort_values(by=['Type', 'SKU'])
is_french = wc_full_data['SKU'].astype(str).str.contains('_fr')
wc_data_french = wc_full_data[is_french]
wc_data = wc_full_data[is_french == False]
# Clean the invalid name
wc_data = wc_data[wc_data['Name'].astype(str).str.contains('#REF!') == False]

# wc_data contains English rows
# wc_data_french contains French Rows

attribute_keys = wc_data.columns[wc_data.columns.str.endswith(' name')]
attribute_values = wc_data.columns[wc_data.columns.str.endswith('value(s)')]

wc_data_attributes = pd.lreshape(
    wc_data, {'key': attribute_keys, 'value': attribute_values})
wc_data_attributes = wc_data_attributes.pivot(
    index='ID', columns='key', values='value')

wc_data = pd.merge(wc_data, wc_data_attributes, on='ID')

wc_data['slug'] = wc_data['Name'].apply(lambda x: slugify(x))

# %%
slug_mask = wc_data['slug'].duplicated(keep=False)
wc_data.loc[slug_mask, ['slug', 'Name']].sort_values(by=['Name'])
wc_data.loc[slug_mask,
            'slug'] += wc_data.groupby('slug').cumcount().add(1).astype(str)
wc_data['new_sku'] = wc_data['SKU'].fillna('').apply(
    lambda x: x.split('-')[0]
)

new_wc_data = wc_data[['slug', 'SKU']
                      ].loc[wc_data['Type'] != 'variation']
jointed = wc_data.join(
    new_wc_data.set_index('SKU'), on='new_sku', rsuffix='_other', lsuffix='_original',)

# %%
# Assign to shopify_data
shopify_data['Handle'] = jointed['slug_other']
shopify_data['Title'] = wc_data['Name']
shopify_data['Variant SKU'] = wc_data['SKU']
shopify_data['Body (HTML)'] = wc_data['Description']
shopify_data['Vendor'] = wc_data['Manufacturer']

wc_data['new_tags'] = wc_data[['Tags', 'Categories']].fillna(value='').apply(
    lambda x: re.split('>|,', (x['Categories']+x['Tags']).strip()), axis=1)
shopify_data['Tags'] = wc_data['new_tags'].apply(
    lambda x: unescape(','.join(np.unique([y.strip() for y in x]))))

published_dict = defaultdict(lambda: 'FALSE')
published_dict[1] = 'TRUE'
shopify_data['Published'] = wc_data['Published'].map(published_dict)
shopify_data['WC Type'] = wc_data['Type']

is_variation = shopify_data['WC Type'] == 'variation'
is_simple = shopify_data['WC Type'] == 'simple'
is_variable = shopify_data['WC Type'] == 'variable'
is_not_variation = shopify_data['WC Type'] != 'variation'


wc_data['Packaging'].fillna(value='')

shopify_data['Option1 Name'] = 'Packaging'
shopify_data['Option1 Value'] = wc_data['Packaging']
shopify_data.loc[is_simple, 'Option1 Name'] = 'Title'
shopify_data.loc[is_simple, 'Option1 Value'] = 'Default Title'

shopify_data['Variant Price'] = wc_data['Regular price']
shopify_data['Variant Compare At Price'] = wc_data['Sale price']
shopify_data['Variant Requires Shipping'] = 'TRUE'

taxable_dict = defaultdict(lambda: 'FALSE')
taxable_dict['taxable'] = 'TRUE'
shopify_data['Variant Taxable'] = wc_data['Tax status'].map(taxable_dict)
shopify_data['Image Src'] = wc_data['Images']
shopify_data['Variant Image'] = wc_data['Images']
shopify_data['Variant Inventory Policy'] = 'continue'
shopify_data['Variant Fulfillment Service'] = 'manual'
shopify_data['Variant Weight Unit'] = 'lb'
shopify_data['Variant Grams'] = wc_data['Weight (lbs)'] * 453.59
shopify_data['Variant Grams'] = shopify_data['Variant Grams'].fillna(
    0).round(0).astype(int)

shopify_data.loc[is_variation, 'Image Src'] = ''
shopify_data.loc[is_variation, 'Title'] = ''
shopify_data.loc[is_variation, 'Body (HTML)'] = ''
shopify_data.loc[is_variation, 'Vendor'] = ''
shopify_data.loc[is_variation, 'Tags'] = ''

shopify_data.loc[is_not_variation, 'Variant Image'] = ''
# %%



empty_columns = pd.DataFrame(
    columns=[
        'Type',
        'Variant Inventory Tracker',
        'Variant Barcode',
        'Variant Tax Code',
        'Image Alt Text',
        'Gift Card',
        'SEO Title',
        'SEO Description',
        'Google Shopping / Google Product Category',
        'Google Shopping / Gender',
        'Google Shopping / Age Group',
        'Google Shopping / MPN',
        'Google Shopping / AdWords Grouping',
        'Google Shopping / AdWords Labels',
        'Google Shopping / Condition',
        'Google Shopping / Custom Product',
        'Google Shopping / Custom Label 0',
        'Google Shopping / Custom Label 1',
        'Google Shopping / Custom Label 2',
        'Google Shopping / Custom Label 3',
        'Google Shopping / Custom Label 4',
        'Option2 Name',
        'Option2 Value',
        'Option3 Name',
        'Option3 Value',
        'Cost per item'])
shopify_data = pd.concat([shopify_data, empty_columns], axis=1)


# Combine variants with its first variations
shopify_data = shopify_data.dropna(axis=0, subset=['Handle'])
shopify_data['Variation Merge'] = shopify_data[['Option1 Value', 'Handle']].fillna(value='').apply(
    lambda x: x['Handle']+'-'+x['Option1 Value'].split(',')[0], axis=1)


first_cols = ['Title', 'Body (HTML)', 'Vendor',
              'Tags', 'Published', 'Image Src', 'Variant SKU']
full_cols = shopify_data.columns.values.tolist()
full_cols.remove('Variation Merge')
last_cols = np.setdiff1d(full_cols, first_cols)

groupby_strategy = {col: 'first' for col in first_cols}
groupby_strategy.update({col: 'last' for col in last_cols})

shopify_data = shopify_data.sort_values(by=['WC Type', 'Variant SKU']).groupby(
    ['Variation Merge'], as_index=False).agg(groupby_strategy)

#%%
is_empty_image = shopify_data['Image Src'].str.len() < 10
shopify_data['Image Position'] = 1
shopify_data.loc[is_empty_image, 'Image Position'] = ''

shopify_data = shopify_data[shopify_example_data.columns.values]
shopify_data.sort_values(by=['Handle', 'Title'],
                         inplace=True, ascending=[True, False])

shopify_data['Variant SKU'] = shopify_data['Variant SKU'].apply(
    lambda x: x.split(':')[1]
)

# %%
shopify_data.to_csv(SHOPIFY_IMPORT_CSV, mode='w+', index=False)
shopify_data


# %%
